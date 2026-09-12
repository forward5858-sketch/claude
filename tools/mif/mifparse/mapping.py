"""Tablo başlıklarını BICD bölümlerine, kolon adlarını veritabanı
alanlarına bağlayan yapılandırma katmanı.

Bu ayrımın sebebi: MIF'in biçimi sabit ama bir kurumun BICD'sindeki
başlık ve kolon adları değişkendir. Gerçek dosya geldiğinde kod değil
`esleme/bicd.varsayilan.json` ayarlanır.
"""

import json
import os
import re

__all__ = ["Mapping", "DEFAULT_CONFIG", "normalize"]

DEFAULT_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "esleme", "bicd.varsayilan.json")

_PUNCT = re.compile(r"[^\w\s]+", re.UNICODE)
_WS = re.compile(r"\s+", re.UNICODE)


def normalize(s):
    """Kolon adlarını karşılaştırılabilir hâle getirir."""
    s = (s or "").replace("\n", " ").replace(" ", " ")
    s = _PUNCT.sub(" ", s)
    return _WS.sub(" ", s).strip().lower()


class Mapping:
    def __init__(self, cfg, path=None):
        self.path = path
        self.sections = []
        for r in cfg.get("bolumler", []):
            self.sections.append({
                "ad": r.get("ad", r.get("desen", "")),
                "re": re.compile(r["desen"]),
                "tip": r["tip"],
                "scope": r.get("scope"),
                "bicd_bolum": r.get("bicd_bolum", ""),
            })
        # {normalize(takma ad): alan}
        self.aliases = {}
        self.fields = []
        for field, names in cfg.get("kolonlar", {}).items():
            self.fields.append(field)
            for nm in names:
                self.aliases.setdefault(normalize(nm), field)

    @classmethod
    def load(cls, path=None):
        path = path or DEFAULT_CONFIG
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f), path)

    # --- bölüm eşlemesi -------------------------------------------------
    def match_section(self, heading):
        """Başlık metnine uyan ilk bölüm kuralı; yoksa None."""
        h = (heading or "").strip()
        for rule in self.sections:
            if rule["re"].search(h):
                return rule
        return None

    # --- kolon eşlemesi -------------------------------------------------
    def match_columns(self, columns):
        """[kolon adı] -> ({kolon adı: alan}, [uyarı]) döndürür."""
        mapped, used, warnings = {}, {}, []
        for col in columns:
            field = self.aliases.get(normalize(col))
            if field is None:
                continue
            if field in used:
                warnings.append(
                    "'%s' ve '%s' kolonlarının ikisi de %s alanına uyuyor; "
                    "ilki kullanıldı." % (used[field], col, field))
                continue
            mapped[col] = field
            used[field] = col
        return mapped, warnings
