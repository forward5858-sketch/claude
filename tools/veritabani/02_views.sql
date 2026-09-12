-- =====================================================================
-- Doğrulama veritabanı — görünümler
-- Kurulum: psql -d dogrulama -f 02_views.sql
-- =====================================================================

SET search_path TO vdb, public;

-- ---------------------------------------------------------------------
-- Sürüm seçimi
-- ---------------------------------------------------------------------

-- Kart başına en son baseline alınmış BICD sürümü. Resmi koşum ve rapor
-- bu sürüme dayanır.
CREATE OR REPLACE VIEW vdb.v_latest_baseline AS
SELECT DISTINCT ON (v.board_id) v.*
  FROM vdb.bicd_version v
 WHERE v.status = 'baselined'
 ORDER BY v.board_id, v.imported_at DESC;

-- Kart başına en son yüklenen sürüm (baseline olmayabilir). Ön çalışma
-- bunu kullanır.
CREATE OR REPLACE VIEW vdb.v_latest_version AS
SELECT DISTINCT ON (v.board_id) v.*
  FROM vdb.bicd_version v
 ORDER BY v.board_id, v.imported_at DESC;

-- ---------------------------------------------------------------------
-- Okunabilir kaynak veri
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW vdb.v_connector AS
SELECT b.project,
       b.name              AS board_name,
       v.doc_number,
       v.revision,
       v.status            AS version_status,
       c.connector_id,
       c.version_id,
       c.connector_name,
       c.scope,
       c.part_number,
       c.mating_part_number,
       c.connector_type,
       c.contact_count,
       c.gender,
       c.location,
       c.source_sections,
       c.doors_object_id,
       c.raw
  FROM vdb.connector c
  JOIN vdb.bicd_version v ON v.version_id = c.version_id
  JOIN vdb.board b        ON b.board_id   = v.board_id;

CREATE OR REPLACE VIEW vdb.v_pin AS
SELECT b.project,
       b.name              AS board_name,
       v.doc_number,
       v.revision,
       v.version_id,
       c.connector_name,
       c.part_number       AS connector_part_number,
       p.pin_id,
       p.connector_id,
       p.pin_index,
       p.name_on_pin,
       p.direction,
       p.related_path_functionality,
       p.scope,
       p.doors_object_id,
       p.raw
  FROM vdb.pin p
  JOIN vdb.connector c    ON c.connector_id = p.connector_id
  JOIN vdb.bicd_version v ON v.version_id   = c.version_id
  JOIN vdb.board b        ON b.board_id     = v.board_id;

-- ---------------------------------------------------------------------
-- Türetilmiş verinin güncel hâli (ekleme-günlüklerinin son satırı)
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW vdb.v_mating_status AS
SELECT c.version_id,
       c.connector_id,
       c.connector_name,
       c.mating_part_number,
       m.result       AS check_result,
       m.source       AS check_source,
       m.source_ref,
       m.checked_by,
       m.checked_at,
       (m.check_id IS NULL)          AS never_checked,
       (m.result IS DISTINCT FROM 'verified') AS needs_attention
  FROM vdb.connector c
  LEFT JOIN LATERAL (
       SELECT * FROM vdb.mating_check mc
        WHERE mc.connector_id = c.connector_id
        ORDER BY mc.checked_at DESC, mc.check_id DESC
        LIMIT 1
  ) m ON TRUE;

CREATE OR REPLACE VIEW vdb.v_pin_interface_current AS
SELECT DISTINCT ON (i.pin_id)
       i.pin_id, i.interface_type, i.rationale, i.assigned_by, i.assigned_at
  FROM vdb.pin_interface i
 ORDER BY i.pin_id, i.assigned_at DESC, i.assignment_id DESC;

-- ---------------------------------------------------------------------
-- Test item ihtiyacının doğrudan girdisi
-- Konnektör başına pin sayısı, yön dağılımı ve kaç ayrı yol/işlev
-- geçtiği — Aşama 4'teki kabiliyet tablosu bu satırlardan çıkar.
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW vdb.v_connector_pin_summary AS
SELECT c.version_id,
       c.connector_id,
       c.connector_name,
       c.scope,
       c.connector_type,
       c.contact_count,
       count(p.pin_id)                                        AS used_pin_count,
       count(*) FILTER (WHERE p.name_on_pin IS NULL
                           OR btrim(p.name_on_pin) = '')      AS unnamed_pin_count,
       count(DISTINCT p.related_path_functionality)           AS distinct_path_count,
       COALESCE(
         (SELECT jsonb_object_agg(d.direction, d.n)
            FROM (SELECT COALESCE(p2.direction, '(boş)') AS direction, count(*) AS n
                    FROM vdb.pin p2
                   WHERE p2.connector_id = c.connector_id
                   GROUP BY 1) d),
         '{}'::jsonb)                                         AS direction_breakdown
  FROM vdb.connector c
  LEFT JOIN vdb.pin p ON p.connector_id = c.connector_id
 GROUP BY c.version_id, c.connector_id, c.connector_name, c.scope,
          c.connector_type, c.contact_count;

-- ---------------------------------------------------------------------
-- Sürümün kalite durumu ve baseline hazırlığı
-- ---------------------------------------------------------------------

CREATE OR REPLACE VIEW vdb.v_version_quality AS
SELECT v.version_id,
       b.project,
       b.name                                              AS board_name,
       v.doc_number,
       v.revision,
       v.status,
       count(q.qc_id)                                      AS check_count,
       count(*) FILTER (WHERE q.result = 'fail')           AS fail_count,
       count(*) FILTER (WHERE q.result = 'fail'
                          AND q.severity = 'soft')         AS soft_fail_count,
       (count(q.qc_id) > 0
        AND count(*) FILTER (WHERE q.result = 'fail') = 0) AS baseline_ready
  FROM vdb.bicd_version v
  JOIN vdb.board b        ON b.board_id = v.board_id
  LEFT JOIN vdb.quality_check q ON q.version_id = v.version_id
 GROUP BY v.version_id, b.project, b.name, v.doc_number, v.revision, v.status;

GRANT SELECT ON ALL TABLES IN SCHEMA vdb TO vdb_reader, vdb_engineer, vdb_loader;
