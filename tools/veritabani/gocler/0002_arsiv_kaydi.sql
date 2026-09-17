-- =====================================================================
-- Göç 0002 — arşiv kütüğü
--
-- Baseline alınan her BICD sürümü kendine yeten bir .sql dosyasına
-- dökülür; o dosyanın kimliği burada durur. Veritabanı kendi
-- arşivlerini bilmeli — CSAR'daki satırın karşılığı bu tablodur.
--
-- SÜRÜMLÜ göç: uygulandıktan sonra değiştirilmez.
-- =====================================================================

SET search_path TO vdb, public;

CREATE TABLE IF NOT EXISTS vdb.archive_record (
  archive_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_id BIGINT      NOT NULL REFERENCES vdb.bicd_version(version_id)
                         ON DELETE RESTRICT,
  filename   TEXT        NOT NULL,
  sha256     CHAR(64)    NOT NULL,
  byte_size  BIGINT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by TEXT        NOT NULL,
  note       TEXT,
  CONSTRAINT archive_record_sha_uq UNIQUE (sha256)
);

COMMENT ON TABLE vdb.archive_record IS
  'Üretilmiş arşiv dosyaları. ON DELETE RESTRICT bilinçli: arşivlenmiş bir sürüm silinemez.';

CREATE INDEX IF NOT EXISTS archive_record_version_ix ON vdb.archive_record (version_id);

GRANT SELECT ON vdb.archive_record TO vdb_reader, vdb_engineer, vdb_loader;
GRANT INSERT ON vdb.archive_record TO vdb_engineer, vdb_loader;
GRANT ALL    ON vdb.archive_record TO vdb_admin;
