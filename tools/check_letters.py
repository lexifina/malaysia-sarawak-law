"""Independent letters-and-digits check of parts against the source PDFs, read by a second engine (xpdf pdftotext -raw).

    python -X utf8 check_letters.py corpus.d/20-ordinances-01.json [...]

Private. Each Act's units (the "# label" lines the build adds left out), word by word and reduced to letters and digits,
must be found in order in the PDF's text from the first body page on, reduced the same way. Between two words the
source may hold only page furniture: page numbers (up to four digits) and the running heads parse.py set aside on those
pages. Anything else is a mismatch: a word not in the PDF, words out of order, or body text left out (also after the
last word). The cover, revision page and arrangement of sections come before the first body page and are not read.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def ld(s: str) -> str:
    return ''.join(ch for ch in s if ch.isalnum())


def source(pdf: Path, first_page: int, end_page: int) -> str:
    out = subprocess.run(['pdftotext', '-raw', '-enc', 'UTF-8', '-f', str(first_page + 1), '-l', str(end_page), str(pdf), '-'],
                         capture_output=True).stdout
    return ld(out.decode('utf-8', 'replace'))


def furniture_only(gap: str, aside: list[str]) -> bool:
    for a in aside:
        if a:
            gap = gap.replace(a, '')
    return re.fullmatch(r'\d{0,4}', gap) is not None or re.fullmatch(r'(\d{1,4})*', gap) is not None and len(gap) <= 8


def check_act(units: dict, S: str, aside_texts: list[str]) -> tuple[bool, str]:
    aside = sorted({ld(a) for a in aside_texts if ld(a)}, key=len, reverse=True)
    pos = 0
    for key, u in units.items():
        for line in u['text'].split('\n'):
            if not line or line.startswith('# '):
                continue
            for w in line.split():
                t = ld(w)
                if not t:
                    continue
                if S.startswith(t, pos):
                    pos += len(t)
                    continue
                # page furniture at this point (a running head or page number): pass over it, then try again
                skipped = True
                while skipped and not S.startswith(t, pos):
                    skipped = False
                    for a in aside:
                        if S.startswith(a, pos):
                            pos += len(a)
                            skipped = True
                            break
                    if not skipped:
                        m = re.match(r'\d{1,4}', S[pos:])
                        if m and S.startswith(t, pos + m.end()):
                            pos += m.end()
                if S.startswith(t, pos):
                    pos += len(t)
                    continue
                i = S.find(t, pos)
                if i < 0:
                    return False, f'{key}: "{w}" not found after source position {pos}'
                if not furniture_only(S[pos:i], aside):
                    return False, f'{key}: before "{w}" the source has "{S[pos:i][:80]}" that is not in the record'
                pos = i + len(t)
    if not furniture_only(S[pos:], aside):
        return False, f'source text after the last unit is not in the record: "{S[pos:pos + 80]}"'
    return True, 'ok'


def main(paths: list[str]) -> int:
    sys.path.insert(0, str(HERE.parent / 'world-law'))
    import pkmy_fetch as F
    import parse as P
    bad = 0
    n = 0
    for p in paths:
        part = json.loads(Path(p).read_text(encoding='utf-8'))
        for act in part['acts']:
            for v in act['versions']:
                pdf = F.path_for(v['source_url'])
                _, meta = P.parse(pdf)
                ok, msg = check_act(v['units'], source(pdf, meta['start_page'], meta['end_page']), meta['aside'])
                n += 1
                if not ok:
                    bad += 1
                    print('MISMATCH', act['slug'], msg)
    print(f'{n} versions checked, {bad} mismatches')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main(sys.argv[1:]))
