"""MIF ağacından tabloları ve her tablonun başlık bağlamını çıkarır.

MIF'te tablolar gövdeden ayrı, `<Tbls>` altında durur; metin akışındaki
paragraflar onlara `<ATbl kimlik>` çapasıyla bağlanır. Bir tablonun hangi
bölüme ait olduğunu ancak çapasının önündeki başlığa bakarak anlarız —
bölüm eşlemesi bu yüzden akış sırasına dayanıyor.
"""

import re

from .mif import para_tables, para_tag, para_text

__all__ = ["Table", "collect_tables", "anchor_map", "tables_in_order",
           "HEADING_NUM_RE", "looks_like_heading"]

# "6.1.1 External Connectors" gibi numaralı başlıklar. Paragraf etiketi
# adları projeden projeye değişir; numaralı desen daha güvenilir.
HEADING_NUM_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+\S")
_HEADING_TAG_RE = re.compile(r"head|title|ba[sş]l[iı]k", re.IGNORECASE)


def looks_like_heading(text, tag):
    return bool(HEADING_NUM_RE.match(text or "")) or bool(_HEADING_TAG_RE.search(tag or ""))


class Table:
    """Bir MIF tablosu: başlıklar ve gövde satırları, hücreler düz metin."""

    __slots__ = ("id", "tag", "title", "header_rows", "body_rows",
                 "heading", "heading_tag", "order")

    def __init__(self, tid):
        self.id = tid
        self.tag = ""
        self.title = ""
        self.header_rows = []
        self.body_rows = []
        self.heading = ""        # çapasının önündeki başlık paragrafı
        self.heading_tag = ""
        self.order = None        # akıştaki sırası; çapasızsa None

    @property
    def columns(self):
        """Başlık satırlarının birleşimi: çok satırlı başlıklar tek ada iner."""
        if not self.header_rows:
            return []
        width = max(len(r) for r in self.header_rows)
        cols = []
        for i in range(width):
            parts = [r[i].strip() for r in self.header_rows
                     if i < len(r) and r[i].strip()]
            cols.append(" ".join(parts))
        return cols

    def rows_as_dicts(self):
        """Gövde satırlarını {kolon adı: değer} sözlüklerine çevirir.

        Adsız ya da tekrar eden kolonlar `kolon_3` gibi konum adıyla
        anılır; hiçbir hücre atılmaz.
        """
        cols, seen, names = self.columns, {}, []
        for i, c in enumerate(cols):
            name = c.strip() or ("kolon_%d" % (i + 1))
            if name in seen:
                seen[name] += 1
                name = "%s_%d" % (name, seen[name])
            else:
                seen[name] = 1
            names.append(name)
        out = []
        for row in self.body_rows:
            d = {}
            for i, val in enumerate(row):
                d[names[i] if i < len(names) else "kolon_%d" % (i + 1)] = val
            out.append(d)
        return out

    def __repr__(self):
        return "<Table %s %r %dx%d>" % (self.id, self.heading,
                                        len(self.body_rows), len(self.columns))


def _cell_text(cell):
    content = cell.first("CellContent")
    if content is None:
        return ""
    parts = [para_text(p) for p in content.all("Para")]
    return "\n".join(p for p in parts if p).strip()


def _rows(section):
    """`<TblH>` / `<TblBody>` altındaki satırları metin listelerine çevirir."""
    out = []
    if section is None:
        return out
    for row in section.all("Row"):
        cells = []
        for cell in row.all("Cell"):
            cells.append(_cell_text(cell))
            span = cell.first("CellColumns")
            if span is not None:
                try:
                    extra = int(span.token() or "1") - 1
                except ValueError:
                    extra = 0
                cells.extend([""] * max(0, extra))
        out.append(cells)
    return out


def collect_tables(root):
    """Belgedeki tüm tabloları {kimlik: Table} olarak döndürür."""
    tables = {}
    for tbl in root.walk("Tbl"):
        tid_node = tbl.first("TblID")
        tid = tid_node.token() if tid_node is not None else ""
        if not tid:
            continue
        t = Table(tid)
        tag = tbl.first("TblTag")
        if tag is not None:
            t.tag = tag.text()
        title = tbl.first("TblTitle")
        if title is not None:
            parts = [para_text(p) for p in title.walk("Para")]
            t.title = " ".join(p for p in parts if p).strip()
        t.header_rows = _rows(tbl.first("TblH"))
        t.body_rows = _rows(tbl.first("TblBody"))
        tables[tid] = t
    return tables


def anchor_map(root, tables):
    """Akıştaki paragrafları dolaşıp her tabloya başlık bağlamını yazar.

    Aynı tablo birden çok kez çapalanmışsa ilk çapa geçerli sayılır.
    """
    order = 0
    heading, heading_tag = "", ""
    for flow in root.walk("TextFlow"):
        for para in flow.walk("Para"):
            text = para_text(para).strip()
            tag = para_tag(para)
            ids = para_tables(para)
            if ids:
                for tid in ids:
                    t = tables.get(tid)
                    if t is not None and t.order is None:
                        t.heading = heading
                        t.heading_tag = heading_tag
                        t.order = order
                        order += 1
            elif text and looks_like_heading(text, tag):
                heading, heading_tag = text, tag
    return tables


def tables_in_order(tables):
    """Akış sırasına göre; çapasız tablolar sona."""
    return sorted(tables.values(),
                  key=lambda t: (t.order is None, t.order or 0, t.id))
