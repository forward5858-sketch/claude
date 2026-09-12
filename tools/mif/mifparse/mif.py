"""MIF (FrameMaker Interchange Format) sözdizimi okuyucu.

Bu katman BICD'den habersizdir: yalnızca MIF dosyasını ağaca çevirir ve
paragraf metnini çıkarır. Belgeye özel her şey üst katmanlarda.

MIF dilbilgisi özeti:

    deyim   := '<' ad ( değer | deyim )* '>'
    dizgi   := '`' ... '\''          (ters tırnak ile başlar, kesme ile biter)
    yorum   := '#' ... satır sonu

Dizgi içi kaçışlar: \\t sekme · \\> büyüktür · \\q kesme · \\Q ters tırnak
· \\\\ ters bölü · \\xNN<boşluk> karakter kodu.
"""

import re

__all__ = ["Node", "read_mif", "parse", "para_text", "para_tag", "para_tables"]


class Node:
    """Bir MIF deyimi: adı, skaler değerleri ve alt deyimleri."""

    __slots__ = ("name", "values", "children")

    def __init__(self, name):
        self.name = name
        self.values = []      # [(tür, metin)] — tür: "s" dizgi, "t" sözcük
        self.children = []

    # --- erişim kolaylıkları -------------------------------------------
    def text(self, default=""):
        """İlk dizgi değeri."""
        for kind, val in self.values:
            if kind == "s":
                return val
        return default

    def token(self, default=""):
        """İlk sözcük değeri (sayı, anahtar sözcük, ölçü)."""
        for kind, val in self.values:
            if kind == "t":
                return val
        return default

    def first(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def all(self, name):
        return [c for c in self.children if c.name == name]

    def walk(self, name=None):
        """Kendisi dahil tüm alt ağacı dolaşır."""
        stack = [self]
        while stack:
            n = stack.pop()
            if name is None or n.name == name:
                yield n
            stack.extend(reversed(n.children))

    def __repr__(self):
        return "<%s %r %d alt>" % (self.name, self.values, len(self.children))


# ----------------------------------------------------------------------
# Dosya okuma ve kodlama
# ----------------------------------------------------------------------

_ENC_RE = re.compile(rb"<MIFEncoding\s+`([^']*)'")


def read_mif(path):
    """MIF dosyasını okur ve (metin, kodlama_adı) döndürür.

    FrameMaker 8 ve sonrası `<MIFEncoding `UTF-8'>` yazar. Daha eskisi
    FrameRoman kullanır; Türkçe karakterler FrameRoman'da yok, o yüzden
    Türkçe içerikli bir BICD'nin UTF-8 export edilmesi gerekir.
    FrameRoman'a mac_roman ile yaklaşıyoruz — gerçek dosyayla sınanacak.
    """
    with open(path, "rb") as f:
        data = f.read()
    m = _ENC_RE.search(data[:8192])
    declared = m.group(1).decode("ascii", "replace") if m else ""
    enc = "utf-8" if declared.upper().replace("_", "-") == "UTF-8" else "mac_roman"
    return data.decode(enc, errors="replace"), (declared or "FrameRoman (varsayıldı)")


# ----------------------------------------------------------------------
# Sözcük ayırma
# ----------------------------------------------------------------------

_WS = " \t\r\n\f\v"
_STOP = _WS + "<>`#"

# FrameRoman kod noktaları için yaklaşık çözüm.
_HEX_DEC = "mac_roman"


def _read_string(src, i, n):
    """`i` açılış ters tırnağını gösterir. (metin, yeni_i) döndürür."""
    i += 1
    out = []
    while i < n:
        c = src[i]
        if c == "'":
            return "".join(out), i + 1
        if c != "\\":
            out.append(c)
            i += 1
            continue
        # kaçış dizisi
        i += 1
        if i >= n:
            break
        e = src[i]
        i += 1
        if e == "t":
            out.append("\t")
        elif e == ">":
            out.append(">")
        elif e == "q":
            out.append("'")
        elif e == "Q":
            out.append("`")
        elif e == "\\":
            out.append("\\")
        elif e == "x":
            hexs = src[i:i + 2]
            if len(hexs) == 2 and all(ch in "0123456789abcdefABCDEF" for ch in hexs):
                i += 2
                if i < n and src[i] == " ":   # kaçışın sonundaki boşluk yutulur
                    i += 1
                try:
                    out.append(bytes([int(hexs, 16)]).decode(_HEX_DEC))
                except Exception:
                    out.append("�")
            else:
                out.append("x")
        else:
            out.append(e)          # tanınmayan kaçış: harfi harfine
    return "".join(out), i


def _scan(src):
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in _WS:
            i += 1
        elif c == "#":
            j = src.find("\n", i)
            i = n if j < 0 else j + 1
        elif c == "<":
            yield ("<", None)
            i += 1
        elif c == ">":
            yield (">", None)
            i += 1
        elif c == "`":
            s, i = _read_string(src, i, n)
            yield ("s", s)
        else:
            j = i
            while j < n and src[j] not in _STOP:
                j += 1
            if j == i:            # tek başına kalmış kesme gibi tuhaflık
                j = i + 1
            yield ("t", src[i:j])
            i = j


def parse(text):
    """MIF metnini kök `Node`'a çevirir."""
    root = Node("MIFFile")
    stack = [root]
    expect_name = False
    for kind, val in _scan(text):
        if kind == "<":
            expect_name = True
        elif kind == ">":
            if expect_name:       # `<>` — bozuk ama tolere et
                expect_name = False
            elif len(stack) > 1:
                stack.pop()
        elif expect_name:
            node = Node(val)
            stack[-1].children.append(node)
            stack.append(node)
            expect_name = False
        else:
            stack[-1].values.append((kind, val))
    return root


# ----------------------------------------------------------------------
# Paragraf metni
# ----------------------------------------------------------------------

# <Char X> adlarının karşılıkları. Listede olmayan ad boş dizgeye düşer.
CHARS = {
    "Tab": "\t", "HardSpace": " ", "NumberSpace": " ", "ThinSpace": " ",
    "EnSpace": " ", "EmSpace": " ", "HardHyphen": "-", "DiscHyphen": "",
    "NoHyphen": "", "HardReturn": "\n", "Cent": "¢", "Pound": "£",
    "Yen": "¥", "EnDash": "–", "EmDash": "—", "Dagger": "†",
    "DoubleDagger": "‡", "Bullet": "•", "SectionSymbol": "§",
    "ParagraphSymbol": "¶", "Trademark": "™", "Registered": "®",
    "Copyright": "©", "Pi": "π",
}

# Metne katkısı olmayan, atlanacak alt deyimler.
_SKIP_IN_LINE = {"Marker", "AFrame", "XRefEnd", "FNote", "Conditional", "Unconditional"}


def para_text(para):
    """Bir `<Para>` düğümünün düz metnini üretir."""
    out = []
    for line in para.all("ParaLine"):
        for c in line.children:
            if c.name == "String":
                out.append(c.text())
            elif c.name == "Char":
                out.append(CHARS.get(c.token(), ""))
            elif c.name in _SKIP_IN_LINE:
                continue
    return "".join(out)


def para_tag(para):
    """`<PgfTag>` değeri; yoksa boş."""
    t = para.first("PgfTag")
    return t.text() if t is not None else ""


def para_tables(para):
    """Paragrafın içindeki `<ATbl>` çapa kimlikleri."""
    return [a.token() for a in para.walk("ATbl") if a.token()]
