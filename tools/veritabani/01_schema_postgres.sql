-- =====================================================================
-- Doğrulama veritabanı — PostgreSQL şeması
-- Kart doğrulama süreci: BICD kaynaklı konnektör ve pin verisi
--
-- Kurulum:  psql -d dogrulama -f 01_schema_postgres.sql
-- Ardından: 02_views.sql, 03_soft_checks.sql
--
-- Tasarım kuralları için: README.md
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS vdb;
SET search_path TO vdb, public;

-- ---------------------------------------------------------------------
-- Sabit sözlükler (enum)
-- ---------------------------------------------------------------------

DO $$ BEGIN
  CREATE TYPE vdb.scope_t          AS ENUM ('external', 'internal');
  CREATE TYPE vdb.version_status_t AS ENUM ('draft', 'verified', 'baselined');
  CREATE TYPE vdb.mating_result_t  AS ENUM ('verified', 'conflict', 'not_found');
  CREATE TYPE vdb.check_severity_t AS ENUM ('hard', 'soft');
  CREATE TYPE vdb.check_result_t   AS ENUM ('pass', 'fail');
  CREATE TYPE vdb.import_status_t  AS ENUM ('running', 'succeeded', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- =====================================================================
-- KATMAN 1 — Çapa: kart ve BICD sürümü
-- Her veri satırı bir BICD sürümüne asılır. Birim kart değil, kartın
-- BICD sürümüdür; koşulmuş bir testin hangi veriye dayandığı sonradan
-- sorulacak.
-- =====================================================================

CREATE TABLE IF NOT EXISTS vdb.board (
  board_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name        TEXT        NOT NULL,
  project     TEXT        NOT NULL,
  description TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT board_uq UNIQUE (project, name)
);

CREATE TABLE IF NOT EXISTS vdb.bicd_version (
  version_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  board_id       BIGINT      NOT NULL REFERENCES vdb.board(board_id) ON DELETE RESTRICT,
  doc_number     TEXT        NOT NULL,               -- BICD doküman numarası
  revision       TEXT        NOT NULL,               -- revizyon / issue
  doors_baseline TEXT,                               -- DOORS baseline adı
  export_date    DATE,
  view_name      TEXT,                               -- export anındaki DOORS view'ı
  mif_filename   TEXT,
  mif_sha256     CHAR(64),                           -- kaynak dosyanın özeti
  status         vdb.version_status_t NOT NULL DEFAULT 'draft',
  imported_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  imported_by    TEXT        NOT NULL,
  note           TEXT,
  CONSTRAINT bicd_version_uq UNIQUE (board_id, doc_number, revision)
);

COMMENT ON COLUMN vdb.bicd_version.view_name IS
  'MIF yalnızca export anında açık olan kolonları yazar; hangi view kullanıldığı verinin eksiksizliğinin kanıtıdır.';

-- =====================================================================
-- KATMAN 2 — Kaynak veri: BICD'den birebir
-- Bu iki tabloya yalnızca yükleyici rol yazar. Elle düzeltilmez;
-- kaynakta hata varsa CR açılır.
-- =====================================================================

CREATE TABLE IF NOT EXISTS vdb.connector (
  connector_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_id         BIGINT      NOT NULL REFERENCES vdb.bicd_version(version_id) ON DELETE CASCADE,
  connector_name     TEXT        NOT NULL,           -- J1, J2 …
  scope              vdb.scope_t NOT NULL,           -- 6.1.1 external / 6.1.2 internal
  part_number        TEXT,                           -- §6.1 — kartın kendi konnektörü
  mating_part_number TEXT,                           -- §8   — karşılığı
  connector_type     TEXT,
  contact_count      INTEGER,
  gender             TEXT,
  location           TEXT,
  doors_object_id    TEXT,
  source_sections    TEXT[]      NOT NULL DEFAULT '{}',  -- {'6.1'} / {'8'} / {'6.1','8'}
  raw                JSONB       NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT connector_uq UNIQUE (version_id, connector_name),
  CONSTRAINT connector_contact_count_ck CHECK (contact_count IS NULL OR contact_count > 0)
);

COMMENT ON COLUMN vdb.connector.source_sections IS
  'Konnektörün BICD''de hangi bölümlerde göründüğü. §6.1 ile §8 örtüşme kontrolü bu kolondan yapılır.';
COMMENT ON COLUMN vdb.connector.raw IS
  'DOORS''un o satırda verdiği TÜM attribute''lar, adıyla ve değeriyle, ham. Adlı kolonlar günlük iş içindir; hiçbir şey atılmaz.';

CREATE TABLE IF NOT EXISTS vdb.pin (
  pin_id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  connector_id               BIGINT      NOT NULL REFERENCES vdb.connector(connector_id) ON DELETE CASCADE,
  pin_index                  TEXT        NOT NULL,   -- metin: "12" de olur "A1" de
  name_on_pin                TEXT,
  direction                  TEXT,
  related_path_functionality TEXT,
  scope                      vdb.scope_t NOT NULL,   -- 6.2.1 external / 6.2.2 internal
  doors_object_id            TEXT,
  raw                        JSONB       NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT pin_uq UNIQUE (connector_id, pin_index)
);

COMMENT ON COLUMN vdb.pin.pin_index IS
  'Metin tipi bilinçli: konnektör pin numaraları alfanümerik olabiliyor (A1, B12).';

-- Yön sözlüğü. Gerçek değerler .mif örneği geldiğinde güncellenecek;
-- yumuşak kontrol bu tabloya bakar, koda gömülü liste yok.
CREATE TABLE IF NOT EXISTS vdb.direction_vocabulary (
  direction   TEXT PRIMARY KEY,
  description TEXT
);

INSERT INTO vdb.direction_vocabulary (direction, description) VALUES
  ('IN',     'Karta giren'),
  ('OUT',    'Karttan çıkan'),
  ('BIDIR',  'Çift yönlü'),
  ('POWER',  'Besleme'),
  ('GROUND', 'Şase / referans'),
  ('NC',     'Bağlı değil'),
  ('SHIELD', 'Ekran')
ON CONFLICT (direction) DO NOTHING;

-- =====================================================================
-- KATMAN 3 — Bizim ürettiğimiz veri
-- Kaynaktan ayrı tablolarda. Denetimde "bu satır BICD'den mi geldi
-- yoksa siz mi türettiniz" sorusu tek kelimeyle cevaplanmalı.
-- Her ikisi de ekleme-günlüğü: düzeltme yeni satırdır, eski silinmez.
-- =====================================================================

CREATE TABLE IF NOT EXISTS vdb.mating_check (
  check_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  connector_id BIGINT      NOT NULL REFERENCES vdb.connector(connector_id) ON DELETE CASCADE,
  result       vdb.mating_result_t NOT NULL,
  source       TEXT        NOT NULL,                 -- üretici kataloğu / dağıtıcı / kurum parça DB
  source_ref   TEXT,                                 -- bağlantı ya da belge numarası
  checked_by   TEXT        NOT NULL,
  checked_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  note         TEXT
);

COMMENT ON TABLE vdb.mating_check IS
  '§8''deki değer BICD''nin; doğrulama sonucu bizim. Aynı konnektör için birden çok kayıt olabilir — en sonuncusu geçerli (v_mating_status), öncekiler silinmez.';

CREATE TABLE IF NOT EXISTS vdb.pin_interface (
  assignment_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  pin_id         BIGINT      NOT NULL REFERENCES vdb.pin(pin_id) ON DELETE CASCADE,
  interface_type TEXT        NOT NULL,
  rationale      TEXT,
  assigned_by    TEXT        NOT NULL,
  assigned_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE vdb.pin_interface IS
  'Aşama 3''ün çıktısı: pinin hangi arayüz tipine düştüğü. BICD''de yazmaz, Related Path Functionality''den türetilir. Arayüz tipi listesi geldiğinde dolar.';

-- =====================================================================
-- KATMAN 4 — Kayıt ve izlenebilirlik
-- =====================================================================

CREATE TABLE IF NOT EXISTS vdb.import_run (
  run_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_id   BIGINT      NOT NULL REFERENCES vdb.bicd_version(version_id) ON DELETE CASCADE,
  tool_version TEXT        NOT NULL,
  source_file  TEXT,
  started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at  TIMESTAMPTZ,
  status       vdb.import_status_t NOT NULL DEFAULT 'running',
  row_counts   JSONB,
  operator     TEXT        NOT NULL,
  log          TEXT
);

CREATE TABLE IF NOT EXISTS vdb.quality_check (
  qc_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_id  BIGINT      NOT NULL REFERENCES vdb.bicd_version(version_id) ON DELETE CASCADE,
  run_id      BIGINT      REFERENCES vdb.import_run(run_id) ON DELETE SET NULL,
  check_code  TEXT        NOT NULL,
  severity    vdb.check_severity_t NOT NULL,
  result      vdb.check_result_t   NOT NULL,
  detail      TEXT,
  ran_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- İndeksler
-- =====================================================================

CREATE INDEX IF NOT EXISTS connector_version_ix  ON vdb.connector (version_id);
CREATE INDEX IF NOT EXISTS connector_raw_ix      ON vdb.connector USING GIN (raw);
CREATE INDEX IF NOT EXISTS pin_connector_ix      ON vdb.pin (connector_id);
CREATE INDEX IF NOT EXISTS pin_name_ix           ON vdb.pin (name_on_pin);
CREATE INDEX IF NOT EXISTS pin_rpf_ix            ON vdb.pin (related_path_functionality);
CREATE INDEX IF NOT EXISTS pin_raw_ix            ON vdb.pin USING GIN (raw);
CREATE INDEX IF NOT EXISTS mating_check_conn_ix  ON vdb.mating_check (connector_id, checked_at DESC);
CREATE INDEX IF NOT EXISTS pin_interface_pin_ix  ON vdb.pin_interface (pin_id, assigned_at DESC);
CREATE INDEX IF NOT EXISTS quality_check_ver_ix  ON vdb.quality_check (version_id, severity, result);

-- =====================================================================
-- Değişmezlik — veritabanı seviyesinde
-- =====================================================================

-- 1) Baseline alınmış bir sürümün kaynak verisi dokunulmazdır.
-- NOT: dallar ayrı deyimler hâlinde yazılmalı. Tek bir CASE ifadesinde
-- toplanırsa plpgsql ifadenin tamamını çözümler ve pin tetikleyicisinde
-- olmayan NEW.version_id alanı yüzünden çalışma anında hata verir.
CREATE OR REPLACE FUNCTION vdb.guard_baselined() RETURNS trigger AS $$
DECLARE
  v_id     BIGINT;
  v_conn   BIGINT;
  v_status vdb.version_status_t;
BEGIN
  IF TG_TABLE_NAME = 'connector' THEN
    IF TG_OP = 'DELETE' THEN v_id := OLD.version_id; ELSE v_id := NEW.version_id; END IF;
  ELSE
    IF TG_OP = 'DELETE' THEN v_conn := OLD.connector_id; ELSE v_conn := NEW.connector_id; END IF;
    SELECT c.version_id INTO v_id FROM vdb.connector c WHERE c.connector_id = v_conn;
  END IF;

  SELECT status INTO v_status FROM vdb.bicd_version WHERE version_id = v_id;
  IF v_status = 'baselined' THEN
    RAISE EXCEPTION
      'Baseline alınmış BICD sürümünün (version_id=%) kaynak verisi değiştirilemez. Yeni revizyon için yeni sürüm açın.', v_id
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;

  IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS connector_baseline_guard ON vdb.connector;
CREATE TRIGGER connector_baseline_guard
  BEFORE INSERT OR UPDATE OR DELETE ON vdb.connector
  FOR EACH ROW EXECUTE FUNCTION vdb.guard_baselined();

DROP TRIGGER IF EXISTS pin_baseline_guard ON vdb.pin;
CREATE TRIGGER pin_baseline_guard
  BEFORE INSERT OR UPDATE OR DELETE ON vdb.pin
  FOR EACH ROW EXECUTE FUNCTION vdb.guard_baselined();

-- 2) Yumuşak kontroller geçmeden bir sürüm baseline'a çıkamaz.
CREATE OR REPLACE FUNCTION vdb.guard_baseline_promotion() RETURNS trigger AS $$
DECLARE
  n_fail INTEGER;
  n_run  INTEGER;
BEGIN
  IF NEW.status = 'baselined' AND OLD.status IS DISTINCT FROM 'baselined' THEN
    SELECT count(*) INTO n_run  FROM vdb.quality_check WHERE version_id = NEW.version_id;
    SELECT count(*) INTO n_fail FROM vdb.quality_check
      WHERE version_id = NEW.version_id AND result = 'fail';
    IF n_run = 0 THEN
      RAISE EXCEPTION 'Bu sürümde hiç kalite kontrolü koşulmamış; baseline alınamaz. Önce vdb.run_soft_checks(%) çalıştırın.', NEW.version_id;
    END IF;
    IF n_fail > 0 THEN
      RAISE EXCEPTION 'Bu sürümde % adet açık kalite bulgusu var; baseline alınamaz.', n_fail;
    END IF;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS bicd_version_baseline_guard ON vdb.bicd_version;
CREATE TRIGGER bicd_version_baseline_guard
  BEFORE UPDATE ON vdb.bicd_version
  FOR EACH ROW EXECUTE FUNCTION vdb.guard_baseline_promotion();

-- =====================================================================
-- Roller ve yetkiler
-- =====================================================================

DO $$
DECLARE r TEXT;
BEGIN
  FOREACH r IN ARRAY ARRAY['vdb_reader','vdb_engineer','vdb_loader','vdb_admin'] LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      EXECUTE format('CREATE ROLE %I NOLOGIN', r);
    END IF;
  END LOOP;
END $$;

GRANT USAGE ON SCHEMA vdb TO vdb_reader, vdb_engineer, vdb_loader, vdb_admin;

-- Okuyucu: her şeyi okur, hiçbir şey yazmaz.
GRANT SELECT ON ALL TABLES IN SCHEMA vdb TO vdb_reader;

-- Mühendis: kaynağı okur, yalnızca bizim tablolarımıza yazar.
GRANT SELECT ON ALL TABLES IN SCHEMA vdb TO vdb_engineer;
GRANT INSERT ON vdb.mating_check, vdb.pin_interface TO vdb_engineer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vdb TO vdb_engineer;

-- Yükleyici: kaynak tablolara yazan tek rol.
GRANT SELECT ON ALL TABLES IN SCHEMA vdb TO vdb_loader;
GRANT INSERT, UPDATE, DELETE ON vdb.board, vdb.bicd_version, vdb.connector, vdb.pin,
                                vdb.import_run, vdb.quality_check TO vdb_loader;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vdb TO vdb_loader;

-- Yönetici.
GRANT ALL ON ALL TABLES IN SCHEMA vdb TO vdb_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA vdb TO vdb_admin;
