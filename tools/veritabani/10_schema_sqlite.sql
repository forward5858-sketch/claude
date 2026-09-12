-- =====================================================================
-- Doğrulama veritabanı — SQLite şeması (baseline arşiv kopyası)
--
-- Bu dosya canlı sistemin değil, ARŞİVİN şemasıdır. Bir BICD sürümü
-- baseline alındığında PostgreSQL'deki o sürüme ait satırlar tek
-- dosyalık bir SQLite veritabanına dökülür; dosyanın SHA-256 özeti ile
-- birlikte CSAR'a konfigürasyon item'ı olarak işlenir.
--
-- Neden SQLite: tek dosya, sunucu gerektirmez, formatı uzun ömürlü.
-- SOI-3 denetiminde on yıl sonra açılabilmesi gereken kanıt bu.
--
-- Arşiv salt okunurdur: rol ve baseline tetikleyicileri yoktur, çünkü
-- dosyanın kendisi dondurulmuştur.
--
-- Kurulum: sqlite3 <kart>_<rev>_bicd.sqlite < 10_schema_sqlite.sql
-- =====================================================================

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS board (
  board_id    INTEGER PRIMARY KEY,
  name        TEXT NOT NULL,
  project     TEXT NOT NULL,
  description TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (project, name)
);

CREATE TABLE IF NOT EXISTS bicd_version (
  version_id     INTEGER PRIMARY KEY,
  board_id       INTEGER NOT NULL REFERENCES board(board_id),
  doc_number     TEXT NOT NULL,
  revision       TEXT NOT NULL,
  doors_baseline TEXT,
  export_date    TEXT,
  view_name      TEXT,
  mif_filename   TEXT,
  mif_sha256     TEXT,
  status         TEXT NOT NULL DEFAULT 'draft'
                 CHECK (status IN ('draft','verified','baselined')),
  imported_at    TEXT NOT NULL DEFAULT (datetime('now')),
  imported_by    TEXT NOT NULL,
  note           TEXT,
  UNIQUE (board_id, doc_number, revision)
);

CREATE TABLE IF NOT EXISTS connector (
  connector_id       INTEGER PRIMARY KEY,
  version_id         INTEGER NOT NULL REFERENCES bicd_version(version_id) ON DELETE CASCADE,
  connector_name     TEXT NOT NULL,
  scope              TEXT NOT NULL CHECK (scope IN ('external','internal')),
  part_number        TEXT,
  mating_part_number TEXT,
  connector_type     TEXT,
  contact_count      INTEGER CHECK (contact_count IS NULL OR contact_count > 0),
  gender             TEXT,
  location           TEXT,
  doors_object_id    TEXT,
  -- PostgreSQL'de TEXT[]; burada JSON dizisi: ["6.1","8"]
  source_sections    TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(source_sections)),
  -- PostgreSQL'de JSONB; burada JSON metni. Ham DOORS attribute'ları.
  raw                TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(raw)),
  UNIQUE (version_id, connector_name)
);

CREATE TABLE IF NOT EXISTS pin (
  pin_id                     INTEGER PRIMARY KEY,
  connector_id               INTEGER NOT NULL REFERENCES connector(connector_id) ON DELETE CASCADE,
  pin_index                  TEXT NOT NULL,
  name_on_pin                TEXT,
  direction                  TEXT,
  related_path_functionality TEXT,
  scope                      TEXT NOT NULL CHECK (scope IN ('external','internal')),
  doors_object_id            TEXT,
  raw                        TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(raw)),
  UNIQUE (connector_id, pin_index)
);

CREATE TABLE IF NOT EXISTS direction_vocabulary (
  direction   TEXT PRIMARY KEY,
  description TEXT
);

CREATE TABLE IF NOT EXISTS mating_check (
  check_id     INTEGER PRIMARY KEY,
  connector_id INTEGER NOT NULL REFERENCES connector(connector_id) ON DELETE CASCADE,
  result       TEXT NOT NULL CHECK (result IN ('verified','conflict','not_found')),
  source       TEXT NOT NULL,
  source_ref   TEXT,
  checked_by   TEXT NOT NULL,
  checked_at   TEXT NOT NULL DEFAULT (datetime('now')),
  note         TEXT
);

CREATE TABLE IF NOT EXISTS pin_interface (
  assignment_id  INTEGER PRIMARY KEY,
  pin_id         INTEGER NOT NULL REFERENCES pin(pin_id) ON DELETE CASCADE,
  interface_type TEXT NOT NULL,
  rationale      TEXT,
  assigned_by    TEXT NOT NULL,
  assigned_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS import_run (
  run_id       INTEGER PRIMARY KEY,
  version_id   INTEGER NOT NULL REFERENCES bicd_version(version_id) ON DELETE CASCADE,
  tool_version TEXT NOT NULL,
  source_file  TEXT,
  started_at   TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at  TEXT,
  status       TEXT NOT NULL DEFAULT 'running'
               CHECK (status IN ('running','succeeded','failed')),
  row_counts   TEXT CHECK (row_counts IS NULL OR json_valid(row_counts)),
  operator     TEXT NOT NULL,
  log          TEXT
);

CREATE TABLE IF NOT EXISTS quality_check (
  qc_id      INTEGER PRIMARY KEY,
  version_id INTEGER NOT NULL REFERENCES bicd_version(version_id) ON DELETE CASCADE,
  run_id     INTEGER REFERENCES import_run(run_id),
  check_code TEXT NOT NULL,
  severity   TEXT NOT NULL CHECK (severity IN ('hard','soft')),
  result     TEXT NOT NULL CHECK (result IN ('pass','fail')),
  detail     TEXT,
  ran_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS connector_version_ix ON connector (version_id);
CREATE INDEX IF NOT EXISTS pin_connector_ix     ON pin (connector_id);
CREATE INDEX IF NOT EXISTS pin_name_ix          ON pin (name_on_pin);
CREATE INDEX IF NOT EXISTS mating_check_conn_ix ON mating_check (connector_id, checked_at DESC);

-- ---------------------------------------------------------------------
-- Denetimde kullanılacak görünümler
-- ---------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS v_connector AS
SELECT b.project, b.name AS board_name, v.doc_number, v.revision,
       c.*
  FROM connector c
  JOIN bicd_version v ON v.version_id = c.version_id
  JOIN board b        ON b.board_id   = v.board_id;

CREATE VIEW IF NOT EXISTS v_pin AS
SELECT b.project, b.name AS board_name, v.doc_number, v.revision,
       c.connector_name, c.part_number AS connector_part_number,
       p.*
  FROM pin p
  JOIN connector c    ON c.connector_id = p.connector_id
  JOIN bicd_version v ON v.version_id   = c.version_id
  JOIN board b        ON b.board_id     = v.board_id;

CREATE VIEW IF NOT EXISTS v_mating_status AS
SELECT c.version_id, c.connector_id, c.connector_name, c.mating_part_number,
       m.result AS check_result, m.source AS check_source, m.source_ref,
       m.checked_by, m.checked_at,
       (m.check_id IS NULL)                        AS never_checked,
       (m.result IS NULL OR m.result <> 'verified') AS needs_attention
  FROM connector c
  LEFT JOIN mating_check m
         ON m.check_id = (SELECT mc.check_id FROM mating_check mc
                           WHERE mc.connector_id = c.connector_id
                           ORDER BY mc.checked_at DESC, mc.check_id DESC LIMIT 1);

CREATE VIEW IF NOT EXISTS v_connector_pin_summary AS
SELECT c.version_id, c.connector_id, c.connector_name, c.scope,
       c.connector_type, c.contact_count,
       count(p.pin_id)                                          AS used_pin_count,
       count(CASE WHEN p.name_on_pin IS NULL
                    OR trim(p.name_on_pin) = '' THEN 1 END)     AS unnamed_pin_count,
       count(DISTINCT p.related_path_functionality)             AS distinct_path_count
  FROM connector c
  LEFT JOIN pin p ON p.connector_id = c.connector_id
 GROUP BY c.version_id, c.connector_id, c.connector_name, c.scope,
          c.connector_type, c.contact_count;
