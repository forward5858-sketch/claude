-- =====================================================================
-- Örnek veri — şemanın şeklinin gözle görülmesi için
--
-- Uydurma bir kart. Gerçek proje verisi değildir; .mif ayrıştırıcısı
-- yazılırken hedef satır yapısının örneği olarak durur.
--
-- Kullanım: psql -d dogrulama -f ornek/ornek_veri.sql
-- =====================================================================

SET search_path TO vdb, public;

BEGIN;

INSERT INTO vdb.board (name, project, description)
VALUES ('AGK-1200', 'ÖRNEK PROJE', 'Arayüz ve giriş/çıkış kartı')
RETURNING board_id \gset board_

INSERT INTO vdb.bicd_version
  (board_id, doc_number, revision, doors_baseline, export_date, view_name,
   mif_filename, mif_sha256, imported_by, note)
VALUES
  (:board_board_id, 'DOC-BICD-AGK1200', 'C', 'BL-2026-03',
   DATE '2026-03-14', 'Verification Export View',
   'AGK-1200_BICD_C.mif',
   'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
   'dogrulama.muh', 'Örnek yükleme — gerçek proje verisi değildir.')
RETURNING version_id \gset ver_

INSERT INTO vdb.import_run (version_id, tool_version, source_file, operator, status, finished_at, row_counts)
VALUES (:ver_version_id, 'mif-import 0.0.0-ornek', 'AGK-1200_BICD_C.mif', 'dogrulama.muh',
        'succeeded', now(), '{"connector": 2, "pin": 11}'::jsonb)
RETURNING run_id \gset run_

-- ---------------------------------------------------------------------
-- §6.1.1 External Connectors + §8 Constraints (mating)
-- ---------------------------------------------------------------------
INSERT INTO vdb.connector
  (version_id, connector_name, scope, part_number, mating_part_number,
   connector_type, contact_count, gender, location, doors_object_id,
   source_sections, raw)
VALUES
  (:ver_version_id, 'J1', 'external', 'DAMA-9S-A197', 'DAMA-9P-A197',
   'D-Sub 9', 9, 'Female', 'Ön panel', 'AGK1200-BICD-000412',
   ARRAY['6.1','8'],
   '{"Connector Name":"J1","Part Number":"DAMA-9S-A197","Type":"D-Sub 9","Contact Count":"9","Gender":"Female","Location":"Ön panel","Mating Part Number":"DAMA-9P-A197","Notes":"RS422 bakım hattı"}'::jsonb)
RETURNING connector_id \gset j1_

-- ---------------------------------------------------------------------
-- §6.1.2 Internal Connectors + §8
-- ---------------------------------------------------------------------
INSERT INTO vdb.connector
  (version_id, connector_name, scope, part_number, mating_part_number,
   connector_type, contact_count, gender, location, doors_object_id,
   source_sections, raw)
VALUES
  (:ver_version_id, 'J2', 'internal', 'PH-10S-VS', 'PH-10P-VS',
   'Header 2.0mm', 10, 'Female', 'Kart üstü', 'AGK1200-BICD-000418',
   ARRAY['6.1','8'],
   '{"Connector Name":"J2","Part Number":"PH-10S-VS","Type":"Header 2.0mm","Contact Count":"10","Gender":"Female","Location":"Kart üstü","Mating Part Number":"PH-10P-VS"}'::jsonb)
RETURNING connector_id \gset j2_

-- ---------------------------------------------------------------------
-- §6.2.1 External Connection List — J1
-- Beş kolon adlı alanlarda, tamamı ayrıca raw'da.
-- ---------------------------------------------------------------------
INSERT INTO vdb.pin
  (connector_id, pin_index, name_on_pin, direction, related_path_functionality,
   scope, doors_object_id, raw)
VALUES
  (:j1_connector_id, '1', 'MAINT_TX_P', 'OUT',   'RS422 bakım hattı — verici', 'external', 'AGK1200-BICD-000501',
   '{"Connector Name":"J1","Pin Index":"1","Name on Pin":"MAINT_TX_P","Direction":"OUT","Related Path Functionality":"RS422 bakım hattı — verici"}'::jsonb),
  (:j1_connector_id, '2', 'MAINT_TX_N', 'OUT',   'RS422 bakım hattı — verici', 'external', 'AGK1200-BICD-000502',
   '{"Connector Name":"J1","Pin Index":"2","Name on Pin":"MAINT_TX_N","Direction":"OUT","Related Path Functionality":"RS422 bakım hattı — verici"}'::jsonb),
  (:j1_connector_id, '3', 'MAINT_RX_P', 'IN',    'RS422 bakım hattı — alıcı',  'external', 'AGK1200-BICD-000503',
   '{"Connector Name":"J1","Pin Index":"3","Name on Pin":"MAINT_RX_P","Direction":"IN","Related Path Functionality":"RS422 bakım hattı — alıcı"}'::jsonb),
  (:j1_connector_id, '4', 'MAINT_RX_N', 'IN',    'RS422 bakım hattı — alıcı',  'external', 'AGK1200-BICD-000504',
   '{"Connector Name":"J1","Pin Index":"4","Name on Pin":"MAINT_RX_N","Direction":"IN","Related Path Functionality":"RS422 bakım hattı — alıcı"}'::jsonb),
  (:j1_connector_id, '5', 'SGND',       'GROUND','Sinyal şasesi',              'external', 'AGK1200-BICD-000505',
   '{"Connector Name":"J1","Pin Index":"5","Name on Pin":"SGND","Direction":"GROUND","Related Path Functionality":"Sinyal şasesi"}'::jsonb);

-- ---------------------------------------------------------------------
-- §6.2.2 Internal Connection List — J2
-- ---------------------------------------------------------------------
INSERT INTO vdb.pin
  (connector_id, pin_index, name_on_pin, direction, related_path_functionality,
   scope, doors_object_id, raw)
VALUES
  (:j2_connector_id, '1', 'VCC_3V3', 'POWER',  'Besleme — 3.3V',            'internal', 'AGK1200-BICD-000611',
   '{"Connector Name":"J2","Pin Index":"1","Name on Pin":"VCC_3V3","Direction":"POWER","Related Path Functionality":"Besleme — 3.3V"}'::jsonb),
  (:j2_connector_id, '2', 'DGND',    'GROUND', 'Dijital şase',              'internal', 'AGK1200-BICD-000612',
   '{"Connector Name":"J2","Pin Index":"2","Name on Pin":"DGND","Direction":"GROUND","Related Path Functionality":"Dijital şase"}'::jsonb),
  (:j2_connector_id, '3', 'I2C_SDA', 'BIDIR',  'I2C — veri hattı',          'internal', 'AGK1200-BICD-000613',
   '{"Connector Name":"J2","Pin Index":"3","Name on Pin":"I2C_SDA","Direction":"BIDIR","Related Path Functionality":"I2C — veri hattı"}'::jsonb),
  (:j2_connector_id, '4', 'I2C_SCL', 'OUT',    'I2C — saat hattı',          'internal', 'AGK1200-BICD-000614',
   '{"Connector Name":"J2","Pin Index":"4","Name on Pin":"I2C_SCL","Direction":"OUT","Related Path Functionality":"I2C — saat hattı"}'::jsonb),
  (:j2_connector_id, '5', 'ALERT_N', 'IN',     'I2C — kesme çıkışı',        'internal', 'AGK1200-BICD-000615',
   '{"Connector Name":"J2","Pin Index":"5","Name on Pin":"ALERT_N","Direction":"IN","Related Path Functionality":"I2C — kesme çıkışı"}'::jsonb),
  (:j2_connector_id, '6', 'RSVD',    'NC',     'Ayrılmış — bağlı değil',    'internal', 'AGK1200-BICD-000616',
   '{"Connector Name":"J2","Pin Index":"6","Name on Pin":"RSVD","Direction":"NC","Related Path Functionality":"Ayrılmış — bağlı değil"}'::jsonb);

-- ---------------------------------------------------------------------
-- Mating doğrulaması — BİZİM verimiz, kaynaktan ayrı tabloda
-- ---------------------------------------------------------------------
INSERT INTO vdb.mating_check (connector_id, result, source, source_ref, checked_by, note)
VALUES
  (:j1_connector_id, 'verified', 'Üretici kataloğu', 'Katalog 2025, s.114', 'dogrulama.muh',
   'DAMA-9P-A197 kataloğda DAMA-9S-A197''in eşleniği olarak listeli.'),
  (:j2_connector_id, 'verified', 'Kurum parça veritabanı', 'PN-KAYIT-8842', 'dogrulama.muh', NULL);

-- ---------------------------------------------------------------------
-- Arayüz tahsisi — Aşama 3'ün çıktısı (arayüz tipi listesi geldiğinde
-- tamamı dolacak; burada iki örnek)
-- ---------------------------------------------------------------------
INSERT INTO vdb.pin_interface (pin_id, interface_type, rationale, assigned_by)
SELECT p.pin_id, 'RS422', 'Related Path Functionality "RS422" içeriyor.', 'dogrulama.muh'
  FROM vdb.pin p
 WHERE p.connector_id = :j1_connector_id
   AND p.related_path_functionality LIKE 'RS422%';

COMMIT;

-- Yumuşak kontrolleri koş, sonra sürümü baseline'a çıkar.
SELECT * FROM vdb.run_soft_checks(:ver_version_id, :run_run_id);
UPDATE vdb.bicd_version SET status = 'baselined' WHERE version_id = :ver_version_id;

\echo '--- Konnektör özeti (test item ihtiyacının girdisi) ---'
SELECT connector_name, scope, contact_count, used_pin_count,
       distinct_path_count, direction_breakdown
  FROM vdb.v_connector_pin_summary ORDER BY connector_name;

\echo '--- Sürüm kalite durumu ---'
SELECT board_name, revision, status, check_count, fail_count, baseline_ready
  FROM vdb.v_version_quality;
