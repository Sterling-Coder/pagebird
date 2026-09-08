"""Check TM entries for page 14 (0-indexed 13) segments - look for Latin words in Korean targets."""
import sys, os, sqlite3, hashlib, re
sys.path.insert(0, os.path.dirname(__file__))
from babel.ingest.pdf import extract_lines
from babel.protect.mathguard import build_segments

_PLACEHOLDER_RE = re.compile(r'⟦[^⟧]*⟧')
_LATIN_WORD_RE = re.compile(r'[A-Za-z]{3,}')

def tm_key(source, src_lang, tgt_lang):
    h = hashlib.sha1(f"{src_lang}|{tgt_lang}|{source}".encode("utf-8"))
    return h.hexdigest()

pdf = "uploads/grade8_clean-c0c3f10c.pdf"
lines = extract_lines(pdf)
segments = build_segments(lines)

# page 14 = 0-indexed 13
pg_segs = [s for s in segments if s.page == 13]
print(f"Segments on page 14: {len(pg_segs)}")

conn = sqlite3.connect("babel_tm.db")
print("\nKorean TM entries for page 14 segments:")
stale = []
for s in pg_segs:
    key = tm_key(s.source, "en", "ko")
    row = conn.execute("SELECT target, engine FROM tm WHERE key=?", (key,)).fetchone()
    if row:
        tgt, eng = row
        # Strip placeholders and check for Latin words
        cleaned = _PLACEHOLDER_RE.sub('', tgt)
        latin = _LATIN_WORD_RE.findall(cleaned)
        if latin:
            stale.append(key)
            print(f"  STALE [{eng}]: src={s.source[:60]!r}")
            print(f"         tgt={tgt[:80]!r}")
            print(f"         latin_words_in_target={latin}")
        else:
            print(f"  OK [{eng}]: src={s.source[:40]!r} -> tgt={tgt[:40]!r}")
    else:
        print(f"  MISS: src={s.source[:60]!r}")

print(f"\nStale TM entries on page 14: {len(stale)}")
conn.close()
