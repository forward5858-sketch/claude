-- =====================================================================
-- TEKRARLANABİLİR — arşiv dökümü
--
-- Bir BICD sürümünün satırlarını INSERT'lere çevirir. ŞEMAYI İÇERMEZ:
-- `vdb.py arsivle` önce göç ve tekrarlanabilir dosyalarını yazar, sonra
-- bu fonksiyonun çıktısını ekler; ortaya çıkan dosya boş bir
-- veritabanına `psql -f` ile iner.
--
-- Yazım kuralı: PostgreSQL'de örtük dizgi birleştirmede yalnızca İLK
-- literal E'...' olabilir, sonrakiler düz '...' olmalı. Bu yüzden tüm
-- biçim dizgileri düz yazılır; satır sonu ayrıca || E'\n' ile eklenir.
--
-- Elle koşmayın:  python3 vdb.py goc --dsn ...
-- =====================================================================

SET search_path TO vdb, public;

CREATE OR REPLACE FUNCTION vdb.archive_data_sql(p_version_id BIGINT)
RETURNS TEXT AS $fn$
DECLARE
  o  TEXT := '';
  nl TEXT := chr(10);
  r  RECORD;
  v  RECORD;
BEGIN
  SELECT bv.*, b.project, b.name AS board_name INTO v
    FROM vdb.bicd_version bv JOIN vdb.board b ON b.board_id = bv.board_id
   WHERE bv.version_id = p_version_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Sürüm bulunamadı: %', p_version_id;
  END IF;
  IF v.status <> 'baselined' THEN
    RAISE EXCEPTION 'Sürüm % baseline alınmamış (durum: %). Arşiv dondurulmuş '
                    'sürümün kaydıdır; taslak arşivlenmez.', p_version_id, v.status;
  END IF;

  o := o || format('-- Veri: %s / %s  %s rev %s', v.project, v.board_name,
                   v.doc_number, v.revision) || nl || nl;
  o := o || 'BEGIN;' || nl || nl || '-- Yön sözlüğü (referans verisi)' || nl;

  FOR r IN SELECT * FROM vdb.direction_vocabulary ORDER BY direction LOOP
    o := o || format('INSERT INTO vdb.direction_vocabulary (direction, description)'
                     ' VALUES (%L, %L) ON CONFLICT (direction) DO NOTHING;',
                     r.direction, r.description) || nl;
  END LOOP;

  o := o || nl || '-- Kart ve sürüm' || nl;
  FOR r IN SELECT b.* FROM vdb.board b WHERE b.board_id = v.board_id LOOP
    o := o || format('INSERT INTO vdb.board (board_id, name, project, description,'
                     ' created_at) OVERRIDING SYSTEM VALUE VALUES (%L, %L, %L, %L, %L);',
                     r.board_id, r.name, r.project, r.description, r.created_at) || nl;
  END LOOP;

  o := o || format('INSERT INTO vdb.bicd_version (version_id, board_id, doc_number,'
                   ' revision, doors_baseline, export_date, view_name, mif_filename,'
                   ' mif_sha256, status, imported_at, imported_by, note)'
                   ' OVERRIDING SYSTEM VALUE VALUES'
                   ' (%L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L);',
                   v.version_id, v.board_id, v.doc_number, v.revision, v.doors_baseline,
                   v.export_date, v.view_name, v.mif_filename, v.mif_sha256,
                   -- Bilerek 'draft': baseline kilidi, sürüm baselined iken
                   -- kaynak satır yazılmasını engeller. Gerçek durum en sonda
                   -- verilir; o sırada terfi kapısı kalite kayıtlarını görmüş olur.
                   'draft',
                   v.imported_at, v.imported_by, v.note) || nl;

  o := o || nl || '-- Konnektörler (§6.1 + §8)' || nl;
  FOR r IN SELECT * FROM vdb.connector WHERE version_id = p_version_id
            ORDER BY connector_id LOOP
    o := o || format('INSERT INTO vdb.connector (connector_id, version_id,'
                     ' connector_name, scope, part_number, mating_part_number,'
                     ' connector_type, contact_count, gender, location, doors_object_id,'
                     ' source_sections, raw) OVERRIDING SYSTEM VALUE VALUES'
                     ' (%L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L, %L);',
                     r.connector_id, r.version_id, r.connector_name, r.scope,
                     r.part_number, r.mating_part_number, r.connector_type,
                     r.contact_count, r.gender, r.location, r.doors_object_id,
                     r.source_sections, r.raw) || nl;
  END LOOP;

  o := o || nl || '-- Pinler (§6.2)' || nl;
  FOR r IN SELECT p.* FROM vdb.pin p JOIN vdb.connector c USING (connector_id)
            WHERE c.version_id = p_version_id ORDER BY p.pin_id LOOP
    o := o || format('INSERT INTO vdb.pin (pin_id, connector_id, pin_index,'
                     ' name_on_pin, direction, related_path_functionality, scope,'
                     ' doors_object_id, raw) OVERRIDING SYSTEM VALUE VALUES'
                     ' (%L, %L, %L, %L, %L, %L, %L, %L, %L);',
                     r.pin_id, r.connector_id, r.pin_index, r.name_on_pin, r.direction,
                     r.related_path_functionality, r.scope, r.doors_object_id,
                     r.raw) || nl;
  END LOOP;

  o := o || nl || '-- Mating doğrulamaları (bizim verimiz)' || nl;
  FOR r IN SELECT m.* FROM vdb.mating_check m JOIN vdb.connector c USING (connector_id)
            WHERE c.version_id = p_version_id ORDER BY m.check_id LOOP
    o := o || format('INSERT INTO vdb.mating_check (check_id, connector_id, result,'
                     ' source, source_ref, checked_by, checked_at, note)'
                     ' OVERRIDING SYSTEM VALUE VALUES (%L, %L, %L, %L, %L, %L, %L, %L);',
                     r.check_id, r.connector_id, r.result, r.source, r.source_ref,
                     r.checked_by, r.checked_at, r.note) || nl;
  END LOOP;

  o := o || nl || '-- Arayüz tahsisleri (Aşama 3 çıktısı)' || nl;
  FOR r IN SELECT i.* FROM vdb.pin_interface i
             JOIN vdb.pin p USING (pin_id) JOIN vdb.connector c USING (connector_id)
            WHERE c.version_id = p_version_id ORDER BY i.assignment_id LOOP
    o := o || format('INSERT INTO vdb.pin_interface (assignment_id, pin_id,'
                     ' interface_type, rationale, assigned_by, assigned_at)'
                     ' OVERRIDING SYSTEM VALUE VALUES (%L, %L, %L, %L, %L, %L);',
                     r.assignment_id, r.pin_id, r.interface_type, r.rationale,
                     r.assigned_by, r.assigned_at) || nl;
  END LOOP;

  o := o || nl || '-- Yükleme ve kalite kayıtları' || nl;
  FOR r IN SELECT * FROM vdb.import_run WHERE version_id = p_version_id
            ORDER BY run_id LOOP
    o := o || format('INSERT INTO vdb.import_run (run_id, version_id, tool_version,'
                     ' source_file, started_at, finished_at, status, row_counts,'
                     ' operator, log) OVERRIDING SYSTEM VALUE VALUES'
                     ' (%L, %L, %L, %L, %L, %L, %L, %L, %L, %L);',
                     r.run_id, r.version_id, r.tool_version, r.source_file, r.started_at,
                     r.finished_at, r.status, r.row_counts, r.operator, r.log) || nl;
  END LOOP;

  FOR r IN SELECT * FROM vdb.quality_check WHERE version_id = p_version_id
            ORDER BY qc_id LOOP
    o := o || format('INSERT INTO vdb.quality_check (qc_id, version_id, run_id,'
                     ' check_code, severity, result, detail, ran_at)'
                     ' OVERRIDING SYSTEM VALUE VALUES (%L, %L, %L, %L, %L, %L, %L, %L);',
                     r.qc_id, r.version_id, r.run_id, r.check_code, r.severity,
                     r.result, r.detail, r.ran_at) || nl;
  END LOOP;

  -- Sürüm gerçek durumuna şimdi alınır. Kalite kayıtları yüklendikten sonra
  -- olmalı: baseline terfi kapısı açık bulgu olmadığını burada doğrular, yani
  -- kurcalanmış bir arşiv baseline olarak geri yüklenemez.
  o := o || nl || '-- Sürümü gerçek durumuna al' || nl;
  o := o || format('UPDATE vdb.bicd_version SET status = %L WHERE version_id = %L;',
                   v.status, v.version_id) || nl;

  -- Kimlik dizileri satırların ötesine alınır; yoksa geri yüklenmiş arşive
  -- yeni satır eklenmek istendiğinde birincil anahtar çakışır.
  o := o || nl || '-- Kimlik dizilerini ilerlet' || nl;
  FOR r IN SELECT * FROM (VALUES
      ('vdb.board', 'board_id'), ('vdb.bicd_version', 'version_id'),
      ('vdb.connector', 'connector_id'), ('vdb.pin', 'pin_id'),
      ('vdb.mating_check', 'check_id'), ('vdb.pin_interface', 'assignment_id'),
      ('vdb.import_run', 'run_id'), ('vdb.quality_check', 'qc_id')
    ) AS t(tablo, kolon) LOOP
    o := o || format('SELECT setval(pg_get_serial_sequence(%L, %L),'
                     ' GREATEST((SELECT COALESCE(MAX(%I), 0) FROM %s), 1));',
                     r.tablo, r.kolon, r.kolon, r.tablo) || nl;
  END LOOP;

  o := o || nl || 'COMMIT;' || nl;
  RETURN o;
END $fn$ LANGUAGE plpgsql;

COMMENT ON FUNCTION vdb.archive_data_sql IS
  'Bir baseline sürümünün satırlarını INSERT''lere çevirir. Şemayı içermez; vdb.py arsivle önüne ekler.';

GRANT EXECUTE ON FUNCTION vdb.archive_data_sql(BIGINT) TO vdb_engineer, vdb_admin;
