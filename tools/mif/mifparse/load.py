"""psycopg ile doğrudan yükleme. Sürücü kurulamayan makinelerde
`emit.build_sql` ile üretilen dosya kullanılır; ikisi aynı kayıtları yazar.
"""

import json

__all__ = ["load"]


def load(ext, meta, dsn):
    import psycopg          # yalnızca bu yol kullanılırsa gerekir

    counts = {"connector": len(ext.connectors), "pin": len(ext.pins)}
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO vdb, public")

            cur.execute("SELECT board_id FROM vdb.board WHERE project=%s AND name=%s",
                        (meta["project"], meta["board"]))
            row = cur.fetchone()
            if row:
                board_id = row[0]
            else:
                cur.execute("INSERT INTO vdb.board (project, name) VALUES (%s,%s) "
                            "RETURNING board_id", (meta["project"], meta["board"]))
                board_id = cur.fetchone()[0]

            cur.execute("SELECT version_id FROM vdb.bicd_version "
                        " WHERE board_id=%s AND doc_number=%s AND revision=%s",
                        (board_id, meta["doc_number"], meta["revision"]))
            row = cur.fetchone()
            if row:
                if not meta.get("fresh"):
                    raise RuntimeError(
                        "Bu BICD sürümü zaten yüklü (version_id=%d). Yeniden "
                        "yüklemek için --taze verin." % row[0])
                cur.execute("DELETE FROM vdb.bicd_version WHERE version_id=%s", (row[0],))

            cur.execute(
                "INSERT INTO vdb.bicd_version (board_id, doc_number, revision,"
                " doors_baseline, export_date, view_name, mif_filename, mif_sha256,"
                " imported_by, note) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                " RETURNING version_id",
                (board_id, meta["doc_number"], meta["revision"], meta.get("doors_baseline"),
                 meta.get("export_date"), meta.get("view_name"), meta.get("mif_filename"),
                 meta.get("mif_sha256"), meta["imported_by"], meta.get("note")))
            version_id = cur.fetchone()[0]

            cur.execute("INSERT INTO vdb.import_run (version_id, tool_version,"
                        " source_file, operator) VALUES (%s,%s,%s,%s) RETURNING run_id",
                        (version_id, meta["tool_version"], meta.get("mif_filename"),
                         meta["imported_by"]))
            run_id = cur.fetchone()[0]

            pins_by_conn = {}
            for p in ext.pins:
                pins_by_conn.setdefault(p["connector_name"].strip().upper(), []).append(p)

            for c in ext.connectors:
                cur.execute(
                    "INSERT INTO vdb.connector (version_id, connector_name, scope,"
                    " part_number, mating_part_number, connector_type, contact_count,"
                    " gender, location, doors_object_id, source_sections, raw)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING connector_id",
                    (version_id, c["connector_name"], c["scope"], c["part_number"],
                     c["mating_part_number"], c["connector_type"], c["contact_count"],
                     c["gender"], c["location"], c["doors_object_id"],
                     c["source_sections"], json.dumps(c["raw"], ensure_ascii=False)))
                connector_id = cur.fetchone()[0]

                rows = pins_by_conn.get(c["connector_name"].strip().upper(), [])
                if rows:
                    cur.executemany(
                        "INSERT INTO vdb.pin (connector_id, pin_index, name_on_pin,"
                        " direction, related_path_functionality, scope, doors_object_id,"
                        " raw) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        [(connector_id, p["pin_index"], p["name_on_pin"], p["direction"],
                          p["related_path_functionality"], p["scope"],
                          p["doors_object_id"], json.dumps(p["raw"], ensure_ascii=False))
                         for p in rows])

            cur.execute("UPDATE vdb.import_run SET status='succeeded',"
                        " finished_at=now(), row_counts=%s WHERE run_id=%s",
                        (json.dumps(counts), run_id))
            cur.execute("SELECT check_code, result, detail FROM vdb.run_soft_checks(%s,%s)",
                        (version_id, run_id))
            checks = cur.fetchall()
        conn.commit()
    return version_id, counts, checks
