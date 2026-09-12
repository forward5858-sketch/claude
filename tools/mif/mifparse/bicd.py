"""Eşlenmiş tablolardan veritabanına yazılacak kayıtları üretir.

Kaynağa sadakat kuralı: adlı alanlara ek olarak her satırın TÜM kolonları
`raw` içinde ham adıyla saklanır. Konnektörün `raw`'ı bölümlere göre
gruplanır (`{"6.1": {...}, "8": {...}}`), çünkü bir konnektör gerçekten
iki ayrı tablodan gelir; pin tek tablodan geldiği için düz sözlüktür.
"""

import re

from .tables import tables_in_order

__all__ = ["Extraction", "extract"]

_INT_RE = re.compile(r"\d+")


def _key(name):
    return (name or "").strip().upper()


def _int_or_none(text):
    m = _INT_RE.search(text or "")
    return int(m.group()) if m else None


def _blank(row):
    return all(not (v or "").strip() for v in row.values())


class Extraction:
    def __init__(self):
        self.connectors = []      # sıra korunur
        self.pins = []
        self.warnings = []
        self.errors = []
        self.tables = []          # (Table, kural or None, eşlenen kolonlar)
        self._by_name = {}

    # --- konnektör kütüğü ----------------------------------------------
    def _connector(self, name, order_hint=None):
        k = _key(name)
        c = self._by_name.get(k)
        if c is None:
            c = {
                "connector_name": (name or "").strip(),
                "scope": None, "part_number": None, "mating_part_number": None,
                "connector_type": None, "contact_count": None, "gender": None,
                "location": None, "doors_object_id": None,
                "source_sections": [], "raw": {},
            }
            self._by_name[k] = c
            self.connectors.append(c)
        return c

    @property
    def stats(self):
        return {
            "connector": len(self.connectors),
            "pin": len(self.pins),
            "warning": len(self.warnings),
            "error": len(self.errors),
        }


def _apply(target, field, value, section, conn_name, ext):
    """Bir alanı yazar; çelişkili ikinci değer uyarı üretir, üzerine yazmaz."""
    value = (value or "").strip() or None
    if value is None:
        return
    old = target.get(field)
    if old is None:
        target[field] = value
    elif old != value:
        ext.warnings.append(
            "%s: %s alanı çelişkili — '%s' (mevcut) / '%s' (§%s). İlki korundu."
            % (conn_name, field, old, value, section))


def extract(tables, mapping):
    """{kimlik: Table} + Mapping -> Extraction."""
    ext = Extraction()

    for tbl in tables_in_order(tables):
        rule = mapping.match_section(tbl.heading)
        colmap, warns = ({}, [])
        if rule is not None:
            colmap, warns = mapping.match_columns(tbl.columns)
            for w in warns:
                ext.warnings.append("Tablo %s (%s): %s" % (tbl.id, tbl.heading, w))
        ext.tables.append((tbl, rule, colmap))
        if rule is None:
            continue

        section = rule["bicd_bolum"]
        need = "connector_name"
        if need not in colmap.values():
            ext.errors.append(
                "Tablo %s — '%s' bölümüne eşleşti ama konnektör adı kolonu "
                "bulunamadı. Kolonlar: %s" % (tbl.id, tbl.heading,
                                              " | ".join(tbl.columns) or "(yok)"))
            continue
        if rule["tip"] == "pin" and "pin_index" not in colmap.values():
            ext.errors.append(
                "Tablo %s — pin listesi ama pin index kolonu bulunamadı. "
                "Kolonlar: %s" % (tbl.id, " | ".join(tbl.columns)))
            continue

        for row in tbl.rows_as_dicts():
            if _blank(row):
                continue
            fields = {colmap[c]: v for c, v in row.items() if c in colmap}
            cname = (fields.get("connector_name") or "").strip()
            if not cname:
                ext.warnings.append(
                    "Tablo %s (%s): konnektör adı boş bir satır atlandı."
                    % (tbl.id, tbl.heading))
                continue

            if rule["tip"] in ("connector", "mating"):
                c = ext._connector(cname)
                if section not in c["source_sections"]:
                    c["source_sections"].append(section)
                c["raw"].setdefault(section, {}).update(row)
                if rule["scope"]:
                    _apply(c, "scope", rule["scope"], section, cname, ext)
                for f in ("part_number", "mating_part_number", "connector_type",
                          "gender", "location", "doors_object_id"):
                    if f in fields:
                        _apply(c, f, fields[f], section, cname, ext)
                if "contact_count" in fields:
                    n = _int_or_none(fields["contact_count"])
                    if n is None and (fields["contact_count"] or "").strip():
                        ext.warnings.append(
                            "%s: kontak sayısı sayıya çevrilemedi ('%s'); boş "
                            "bırakıldı, ham değer raw'da." % (cname, fields["contact_count"]))
                    elif n is not None and c["contact_count"] is None:
                        c["contact_count"] = n

            else:   # pin
                idx = (fields.get("pin_index") or "").strip()
                if not idx:
                    ext.warnings.append(
                        "Tablo %s: %s konnektöründe pin index'i boş bir satır atlandı."
                        % (tbl.id, cname))
                    continue
                c = ext._connector(cname)
                if not c["source_sections"] and section not in c["source_sections"]:
                    # 6.1'de görülmemiş bir konnektöre pin geldi
                    c["source_sections"].append(section)
                    ext.warnings.append(
                        "%s konnektörü yalnızca pin listesinde geçiyor (§6.1'de yok); "
                        "taslak satır açıldı — SC01/SC02 bunu bulgu olarak işaretleyecek."
                        % cname)
                if c["scope"] is None and rule["scope"]:
                    c["scope"] = rule["scope"]
                ext.pins.append({
                    "connector_name": c["connector_name"],
                    "pin_index": idx,
                    "name_on_pin": (fields.get("name_on_pin") or "").strip() or None,
                    "direction": (fields.get("direction") or "").strip() or None,
                    "related_path_functionality":
                        (fields.get("related_path_functionality") or "").strip() or None,
                    "scope": rule["scope"] or c["scope"] or "external",
                    "doors_object_id": (fields.get("doors_object_id") or "").strip() or None,
                    "raw": dict(row),
                })

    # --- yüklemeden önce yakalanan sert ihlaller ------------------------
    seen = {}
    for p in ext.pins:
        k = (_key(p["connector_name"]), p["pin_index"])
        if k in seen:
            ext.errors.append(
                "Tekrar eden pin: %s pin %s iki kez geçiyor. Veritabanı bunu "
                "zaten reddeder; kaynakta düzeltilmeli."
                % (p["connector_name"], p["pin_index"]))
        seen[k] = True

    for c in ext.connectors:
        if c["scope"] is None:
            c["scope"] = "external"
            ext.warnings.append(
                "%s: external/internal belirlenemedi, 'external' varsayıldı."
                % c["connector_name"])

    return ext
