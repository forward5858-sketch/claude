-- =====================================================================
-- Doğrulama veritabanı — yumuşak kontroller
--
-- Sert kontroller (FK, tekillik, zorunlu alan) veritabanı kısıtlarıdır:
-- ihlal edilirse yükleme reddedilir. Buradakiler yumuşaktır: kaynak
-- dokümanın eksiği yüklemeyi başarısız etmez ama kayda geçer ve
-- giderilmeden sürüm baseline'a çıkamaz.
--
-- Kullanım:  SELECT * FROM vdb.run_soft_checks(<version_id>, <run_id>);
-- Kurulum:   psql -d dogrulama -f 03_soft_checks.sql
-- =====================================================================

SET search_path TO vdb, public;

-- Bir kontrolün sonucunu quality_check'e yazar. Boş liste = geçti.
CREATE OR REPLACE FUNCTION vdb._record_check(
  p_version_id BIGINT,
  p_run_id     BIGINT,
  p_code       TEXT,
  p_label      TEXT,
  p_offenders  TEXT[]
) RETURNS BOOLEAN AS $$
DECLARE
  n INTEGER := COALESCE(array_length(p_offenders, 1), 0);
BEGIN
  INSERT INTO vdb.quality_check (version_id, run_id, check_code, severity, result, detail)
  VALUES (
    p_version_id, p_run_id, p_code, 'soft',
    CASE WHEN n = 0 THEN 'pass' ELSE 'fail' END::vdb.check_result_t,
    CASE WHEN n = 0
         THEN p_label || ' — geçti'
         ELSE p_label || ' — ' || n || ' kayıt: ' ||
              array_to_string(p_offenders[1:25], ', ') ||
              CASE WHEN n > 25 THEN ' … (+' || (n - 25) || ')' ELSE '' END
    END
  );
  RETURN n = 0;
END $$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------
-- Bir BICD sürümünün tüm yumuşak kontrollerini koşar.
-- Aynı sürüm için önceki yumuşak sonuçları siler; sert sonuçlara dokunmaz.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION vdb.run_soft_checks(
  p_version_id BIGINT,
  p_run_id     BIGINT DEFAULT NULL
) RETURNS TABLE (check_code TEXT, result vdb.check_result_t, detail TEXT) AS $$
BEGIN
  DELETE FROM vdb.quality_check q
   WHERE q.version_id = p_version_id AND q.severity = 'soft';

  -- SC01/SC02 — §6.1 ile §8 örtüşmesi. Aynı konnektörler iki bölümde de
  -- geçmeli; birinde eksikse kaynakta boşluk var.
  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC01',
    'Konnektör §8''de var ama §6.1''de yok',
    ARRAY(SELECT c.connector_name FROM vdb.connector c
           WHERE c.version_id = p_version_id
             AND NOT ('6.1' = ANY (c.source_sections)) ORDER BY 1));

  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC02',
    'Konnektör §6.1''de var ama §8''de yok',
    ARRAY(SELECT c.connector_name FROM vdb.connector c
           WHERE c.version_id = p_version_id
             AND NOT ('8' = ANY (c.source_sections)) ORDER BY 1));

  -- SC03/SC04 — part number eksikleri. §8 hatası tüm süreci etkiler:
  -- yanlış sipariş, uymayan ITA/Breakout Board.
  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC03',
    'Kartın kendi part number''ı boş (§6.1)',
    ARRAY(SELECT c.connector_name FROM vdb.connector c
           WHERE c.version_id = p_version_id
             AND (c.part_number IS NULL OR btrim(c.part_number) = '') ORDER BY 1));

  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC04',
    'Mating part number boş (§8)',
    ARRAY(SELECT c.connector_name FROM vdb.connector c
           WHERE c.version_id = p_version_id
             AND (c.mating_part_number IS NULL OR btrim(c.mating_part_number) = '') ORDER BY 1));

  -- SC05 — pin listesi hiç olmayan konnektör.
  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC05',
    'Konnektörün §6.2''de hiç pin satırı yok',
    ARRAY(SELECT c.connector_name FROM vdb.connector c
           WHERE c.version_id = p_version_id
             AND NOT EXISTS (SELECT 1 FROM vdb.pin p WHERE p.connector_id = c.connector_id)
           ORDER BY 1));

  -- SC06 — sinyal adı boş pin.
  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC06',
    'Name on Pin boş',
    ARRAY(SELECT c.connector_name || '.' || p.pin_index
            FROM vdb.pin p JOIN vdb.connector c ON c.connector_id = p.connector_id
           WHERE c.version_id = p_version_id
             AND (p.name_on_pin IS NULL OR btrim(p.name_on_pin) = '') ORDER BY 1));

  -- SC07 — sözlük dışı yön değeri. Sözlük vdb.direction_vocabulary
  -- tablosunda; gerçek değerler .mif örneğiyle güncellenecek.
  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC07',
    'Direction değeri sözlükte yok',
    ARRAY(SELECT DISTINCT c.connector_name || '.' || p.pin_index || ' = ' || COALESCE(p.direction, '(boş)')
            FROM vdb.pin p JOIN vdb.connector c ON c.connector_id = p.connector_id
           WHERE c.version_id = p_version_id
             AND (p.direction IS NULL
                  OR NOT EXISTS (SELECT 1 FROM vdb.direction_vocabulary d
                                  WHERE upper(d.direction) = upper(btrim(p.direction))))
           ORDER BY 1));

  -- SC08 — kullanılan pin sayısı konnektörün kontak sayısını aşıyor.
  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC08',
    'Kullanılan pin sayısı kontak sayısını aşıyor',
    ARRAY(SELECT s.connector_name || ' (' || s.used_pin_count || '/' || s.contact_count || ')'
            FROM vdb.v_connector_pin_summary s
           WHERE s.version_id = p_version_id
             AND s.contact_count IS NOT NULL
             AND s.used_pin_count > s.contact_count ORDER BY 1));

  -- SC09 — Related Path Functionality boş. Arayüz tahsisinin (Aşama 3)
  -- dayandığı kolon; boşsa o pin arayüze düşmez.
  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC09',
    'Related Path Functionality boş',
    ARRAY(SELECT c.connector_name || '.' || p.pin_index
            FROM vdb.pin p JOIN vdb.connector c ON c.connector_id = p.connector_id
           WHERE c.version_id = p_version_id
             AND (p.related_path_functionality IS NULL
                  OR btrim(p.related_path_functionality) = '') ORDER BY 1));

  -- SC10 — pinin external/internal kapsamı konnektörünkiyle çelişiyor.
  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC10',
    'Pin kapsamı konnektör kapsamıyla çelişiyor',
    ARRAY(SELECT c.connector_name || '.' || p.pin_index
            FROM vdb.pin p JOIN vdb.connector c ON c.connector_id = p.connector_id
           WHERE c.version_id = p_version_id AND p.scope <> c.scope ORDER BY 1));

  -- SC11 — DOORS nesne kimliği yok: kaynağa geri iz sürülemiyor.
  PERFORM vdb._record_check(p_version_id, p_run_id, 'SC11',
    'DOORS nesne kimliği boş (pin)',
    ARRAY(SELECT c.connector_name || '.' || p.pin_index
            FROM vdb.pin p JOIN vdb.connector c ON c.connector_id = p.connector_id
           WHERE c.version_id = p_version_id
             AND (p.doors_object_id IS NULL OR btrim(p.doors_object_id) = '') ORDER BY 1));

  RETURN QUERY
    SELECT q.check_code, q.result, q.detail
      FROM vdb.quality_check q
     WHERE q.version_id = p_version_id AND q.severity = 'soft'
     ORDER BY q.check_code;
END $$ LANGUAGE plpgsql;

COMMENT ON FUNCTION vdb.run_soft_checks IS
  'Bir BICD sürümünün yumuşak kontrollerini koşar ve sonucu quality_check''e yazar. Tümü geçmeden sürüm baseline''a çıkamaz (bicd_version_baseline_guard).';

GRANT EXECUTE ON FUNCTION vdb.run_soft_checks(BIGINT, BIGINT) TO vdb_loader, vdb_engineer;
