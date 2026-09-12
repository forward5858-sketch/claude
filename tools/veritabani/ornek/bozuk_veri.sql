-- =====================================================================
-- Kasıtlı bozuk örnek — kontrollerin gerçekten çalıştığını gösterir
--
-- İki şey kanıtlanır:
--   1) SERT kontrol: aynı (konnektör, pin_index) ikilisi yüklemeyi
--      reddeder — işlem geri alınır, yarım veri kalmaz.
--   2) YUMUŞAK kontrol: §8'de karşılığı olmayan konnektör yüklemeyi
--      durdurmaz ama bulgu olarak yazılır ve sürüm baseline'a çıkamaz.
--
-- Kullanım: psql -d dogrulama -f ornek/bozuk_veri.sql
-- =====================================================================

SET search_path TO vdb, public;

INSERT INTO vdb.board (name, project, description)
VALUES ('AGK-1300', 'ÖRNEK PROJE', 'Bozuk yükleme denemesi için')
RETURNING board_id \gset bad_board_

INSERT INTO vdb.bicd_version (board_id, doc_number, revision, imported_by)
VALUES (:bad_board_board_id, 'DOC-BICD-AGK1300', 'A', 'dogrulama.muh')
RETURNING version_id \gset bad_ver_

-- ---------------------------------------------------------------------
-- 1) SERT KONTROL — tekrar eden pin_index
-- ---------------------------------------------------------------------
\echo ''
\echo '=== 1) Sert kontrol: aynı pin_index iki kez ==='
\echo 'Beklenen: HATA (duplicate key) ve işlemin tamamının geri alınması.'
\echo ''

BEGIN;
INSERT INTO vdb.connector (version_id, connector_name, scope, part_number,
                           mating_part_number, contact_count, source_sections)
VALUES (:bad_ver_version_id, 'J9', 'external', 'PN-AAA', 'PN-BBB', 4, ARRAY['6.1','8'])
RETURNING connector_id \gset bad_j9_

INSERT INTO vdb.pin (connector_id, pin_index, name_on_pin, direction,
                     related_path_functionality, scope, doors_object_id)
VALUES (:bad_j9_connector_id, '1', 'SIG_A', 'IN', 'Örnek yol', 'external', 'OBJ-1'),
       (:bad_j9_connector_id, '1', 'SIG_B', 'IN', 'Örnek yol', 'external', 'OBJ-2');
COMMIT;

\echo 'Yükleme reddedildiyse aşağıdaki sayı 0 olmalı:'
SELECT count(*) AS yuklenen_konnektor
  FROM vdb.connector WHERE version_id = :bad_ver_version_id;

-- ---------------------------------------------------------------------
-- 2) YUMUŞAK KONTROL — §8'de karşılığı olmayan konnektör
-- ---------------------------------------------------------------------
\echo ''
\echo '=== 2) Yumuşak kontrol: §6.1''de var, §8''de yok ==='
\echo 'Beklenen: yükleme GEÇER, SC02 fail düşer, baseline REDDEDİLİR.'
\echo ''

BEGIN;
INSERT INTO vdb.connector (version_id, connector_name, scope, part_number,
                           mating_part_number, contact_count, source_sections)
VALUES (:bad_ver_version_id, 'J9', 'external', 'PN-AAA', NULL, 4, ARRAY['6.1'])
RETURNING connector_id \gset ok_j9_

INSERT INTO vdb.pin (connector_id, pin_index, name_on_pin, direction,
                     related_path_functionality, scope, doors_object_id)
VALUES (:ok_j9_connector_id, '1', 'SIG_A', 'IN', 'Örnek yol', 'external', 'OBJ-1'),
       (:ok_j9_connector_id, '2', 'SIG_B', 'IN', 'Örnek yol', 'external', 'OBJ-2');
COMMIT;

SELECT check_code, result, detail
  FROM vdb.run_soft_checks(:bad_ver_version_id)
 WHERE result = 'fail';

\echo ''
\echo 'Baseline denemesi — reddedilmeli:'
UPDATE vdb.bicd_version SET status = 'baselined' WHERE version_id = :bad_ver_version_id;

\echo ''
\echo 'Sürüm hâlâ draft olmalı:'
SELECT revision, status, fail_count, baseline_ready
  FROM vdb.v_version_quality WHERE version_id = :bad_ver_version_id;
