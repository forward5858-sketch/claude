"""Çıkarılan kayıtları tek işlemlik (transaction) SQL'e çevirir.

Neden SQL dosyası: kısıtlı bir kurum makinesinde Python sürücüsü
kurulamayabilir. Üretilen dosya yalnızca `psql -f` ile yüklenir, başka
hiçbir şey gerektirmez. Sürücü varsa `load.py` doğrudan yükler; ikisi de
aynı kayıtları yazar.
"""

import json

__all__ = ["build_sql", "TAG"]

TAG = "mifload"          # dolar tırnak etiketi


def lit(v):
    """PostgreSQL dizgi/sayı sabiti. standard_conforming_strings açık varsayılır."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, int):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def jsonb(obj):
    return lit(json.dumps(obj, ensure_ascii=False, sort_keys=True)) + "::jsonb"


def textarr(items):
    if not items:
        return "ARRAY[]::text[]"
    return "ARRAY[" + ", ".join(lit(i) for i in items) + "]::text[]"


def _check_tag(sql_parts):
    """İçerikte dolar tırnak etiketi geçiyorsa çakışmayan bir tane seç."""
    body = "".join(sql_parts)
    tag = TAG
    n = 0
    while ("$%s$" % tag) in body:
        n += 1
        tag = "%s%d" % (TAG, n)
    return tag


def build_sql(ext, meta):
    """Extraction + üstveri -> tek işlemlik SQL metni."""
    b = []
    a = b.append

    a("INSERT INTO vdb.bicd_version\n"
      "    (board_id, doc_number, revision, doors_baseline, export_date,\n"
      "     view_name, mif_filename, mif_sha256, imported_by, note)\n"
      "  VALUES (v_board, %s, %s, %s, %s, %s, %s, %s, %s, %s)\n"
      "  RETURNING version_id INTO v_ver;\n"
      % (lit(meta["doc_number"]), lit(meta["revision"]), lit(meta.get("doors_baseline")),
         (lit(meta["export_date"]) + "::date") if meta.get("export_date") else "NULL",
         lit(meta.get("view_name")), lit(meta.get("mif_filename")),
         lit(meta.get("mif_sha256")), lit(meta["imported_by"]), lit(meta.get("note"))))

    a("INSERT INTO vdb.import_run (version_id, tool_version, source_file, operator)\n"
      "  VALUES (v_ver, %s, %s, %s) RETURNING run_id INTO v_run;\n"
      % (lit(meta["tool_version"]), lit(meta.get("mif_filename")), lit(meta["imported_by"])))

    pins_by_conn = {}
    for p in ext.pins:
        pins_by_conn.setdefault(p["connector_name"].strip().upper(), []).append(p)

    for c in ext.connectors:
        a("\nINSERT INTO vdb.connector\n"
          "    (version_id, connector_name, scope, part_number, mating_part_number,\n"
          "     connector_type, contact_count, gender, location, doors_object_id,\n"
          "     source_sections, raw)\n"
          "  VALUES (v_ver, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\n"
          "  RETURNING connector_id INTO v_conn;\n"
          % (lit(c["connector_name"]), lit(c["scope"]) + "::vdb.scope_t",
             lit(c["part_number"]), lit(c["mating_part_number"]),
             lit(c["connector_type"]), lit(c["contact_count"]), lit(c["gender"]),
             lit(c["location"]), lit(c["doors_object_id"]),
             textarr(c["source_sections"]), jsonb(c["raw"])))

        rows = pins_by_conn.get(c["connector_name"].strip().upper(), [])
        if not rows:
            continue
        vals = []
        for p in rows:
            vals.append("    (v_conn, %s, %s, %s, %s, %s, %s, %s)"
                        % (lit(p["pin_index"]), lit(p["name_on_pin"]),
                           lit(p["direction"]), lit(p["related_path_functionality"]),
                           lit(p["scope"]) + "::vdb.scope_t",
                           lit(p["doors_object_id"]), jsonb(p["raw"])))
        a("INSERT INTO vdb.pin\n"
          "    (connector_id, pin_index, name_on_pin, direction,\n"
          "     related_path_functionality, scope, doors_object_id, raw)\n"
          "  VALUES\n" + ",\n".join(vals) + ";\n")

    a("\nUPDATE vdb.import_run\n"
      "   SET status = 'succeeded', finished_at = now(), row_counts = %s\n"
      " WHERE run_id = v_run;\n"
      % jsonb({"connector": len(ext.connectors), "pin": len(ext.pins)}))
    a("PERFORM vdb.run_soft_checks(v_ver, v_run);\n")

    body = "".join(b)
    tag = _check_tag(b)

    exists = ("SELECT version_id INTO v_old FROM vdb.bicd_version\n"
              "   WHERE board_id = v_board AND doc_number = %s AND revision = %s;\n"
              % (lit(meta["doc_number"]), lit(meta["revision"])))
    if meta.get("fresh"):
        onexists = ("IF v_old IS NOT NULL THEN\n"
                    "    DELETE FROM vdb.bicd_version WHERE version_id = v_old;\n"
                    "  END IF;\n")
    else:
        onexists = ("IF v_old IS NOT NULL THEN\n"
                    "    -- Bu dizgi %-biçimlemeden geçmiyor; plpgsql yer tutucusu tek % olmalı.\n"
                    "    RAISE EXCEPTION 'Bu BICD sürümü zaten yüklü (version_id=%). "
                    "Yeniden yüklemek için --taze verin.', v_old;\n"
                    "  END IF;\n")

    head = (
        "-- Bu dosya BICD .mif export'undan üretildi. Elle düzenlemeyin.\n"
        "-- Kaynak      : %s\n"
        "-- SHA-256     : %s\n"
        "-- Üreten      : %s\n"
        "-- Konnektör/pin: %d / %d\n"
        "--\n"
        "-- Yükleme: psql -d <veritabani> -v ON_ERROR_STOP=1 -f <bu dosya>\n"
        "\n"
        "SET standard_conforming_strings = on;\n"
        "SET search_path TO vdb, public;\n"
        "\n"
        "BEGIN;\n"
        "\n"
        "DO $%s$\n"
        "DECLARE\n"
        "  v_board BIGINT;\n"
        "  v_ver   BIGINT;\n"
        "  v_old   BIGINT;\n"
        "  v_run   BIGINT;\n"
        "  v_conn  BIGINT;\n"
        "BEGIN\n"
        "  SELECT board_id INTO v_board FROM vdb.board\n"
        "   WHERE project = %s AND name = %s;\n"
        "  IF v_board IS NULL THEN\n"
        "    INSERT INTO vdb.board (project, name) VALUES (%s, %s)\n"
        "      RETURNING board_id INTO v_board;\n"
        "  END IF;\n"
        "\n"
        "  %s"
        "  %s"
        "\n"
        % (meta.get("mif_filename") or "?", meta.get("mif_sha256") or "?",
           meta["tool_version"], len(ext.connectors), len(ext.pins),
           tag,
           lit(meta["project"]), lit(meta["board"]),
           lit(meta["project"]), lit(meta["board"]),
           exists, onexists))

    tail = ("END\n$%s$;\n"
            "\n"
            "COMMIT;\n"
            "\n"
            "-- Yükleme raporu\n"
            "SELECT check_code, result, detail\n"
            "  FROM vdb.quality_check q\n"
            "  JOIN vdb.bicd_version v USING (version_id)\n"
            "  JOIN vdb.board b USING (board_id)\n"
            " WHERE b.project = %s AND b.name = %s\n"
            "   AND v.doc_number = %s AND v.revision = %s\n"
            " ORDER BY (result = 'fail') DESC, check_code;\n"
            % (tag, lit(meta["project"]), lit(meta["board"]),
               lit(meta["doc_number"]), lit(meta["revision"])))

    indented = "\n".join(("  " + ln) if ln.strip() else ln for ln in body.split("\n"))
    return head + indented + "\n" + tail
