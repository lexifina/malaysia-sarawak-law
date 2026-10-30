"""Parse one Sarawak LawNet reprint PDF (Word-made "online version of updated text of reprint") into units.

    python -X utf8 parse.py <pdf>            # print the units

Private. Layout (learned from the cache, 2026-10-30): a cover page ("Incorporating all amendments up to <date>"), an
optional revision page, the ARRANGEMENT OF SECTIONS, then the body. Running heads sit above y=135: the page number at
12pt and the short title or "CAP. n" at 8pt. A section is a bold heading row at the left margin, then a row starting
with the bold section number ("8." or "9.—(1)"). Amendment notes ("[Am. Ord. No. 3/60.]") are italic rows of their own.
Schedules start with a bold "SCHEDULE" row. Nothing is reworded: spans of a row are joined, spaces are collapsed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf

TOP = 135.0
SCHEDULE_STREAM = False  # superseded by STREAM_ROWS
# 2026-10-31 (parts after 20-ordinances-02): every page is read in the order the PDF draws its lines, as the independent
# pdftotext -raw reading does; a table is then read cell by cell (a cell's wrapped lines together) instead of row by row
# across its cells. Lines drawn one after another on one baseline stay one row ("8." and its text).
STREAM_ROWS = True
BOTTOM = 805.0
MONTHS = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
                                      'september', 'october', 'november', 'december'], 1)}
SECNO = re.compile(r'^(\d{1,3}[A-Z]{0,3})\s*\.')
SCHED = re.compile(r'^(?:(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH)\s+)?'
                   r'SCHEDULES?\b', re.I)


def norm(s: str) -> str:
    s = s.replace(' ', ' ').replace(' ', ' ').replace(' ', ' ').replace(' ', ' ')
    s = s.replace('⎯', '—')  # the reprints print the em dash as U+23AF (horizontal line extension)
    return re.sub(r'\s+', ' ', s).strip()


def date_of(text: str) -> str | None:
    m = re.search(r'(\d{1,2})\s*(?:st|nd|rd|th)?\s+([A-Za-z]+)\s*,?\s*(\d{4})', text)
    if not m or m.group(2).lower() not in MONTHS:
        return None
    d, mo, y = int(m.group(1)), MONTHS[m.group(2).lower()], int(m.group(3))
    return f'{y:04d}-{mo:02d}-{d:02d}' if 1 <= d <= 31 else None


def rows_of(page) -> tuple[list[dict], list[str]]:
    """Rows (lines at one height joined left to right) inside the body zone, and the running-head texts left out."""
    lines = []
    n = 0
    for b in page.get_text('dict', flags=pymupdf.TEXT_PRESERVE_WHITESPACE)['blocks']:
        for l in b.get('lines', []):
            n += 1
            spans = [s for s in l['spans'] if s['text'].strip()]
            if not spans:
                continue
            if abs(l['dir'][1]) > 0.1:
                continue  # rotated text
            lines.append({'x0': l['bbox'][0], 'y0': l['bbox'][1], 'y1': l['bbox'][3], 'spans': spans, 'n': n})
    if not STREAM_ROWS:
        lines.sort(key=lambda l: (round(l['y1']), l['x0']))
    rows: list[dict] = []
    for l in lines:
        # drawing order: a line joins the row before it only when drawn right after it on the same baseline
        if rows and abs(rows[-1]['y1'] - l['y1']) < 3.5 and (not STREAM_ROWS or l['x0'] >= rows[-1]['lines'][-1]['x0']):
            rows[-1]['spans'] += l['spans']
            rows[-1]['x0'] = min(rows[-1]['x0'], l['x0'])
            rows[-1]['lines'].append(l)
        else:
            rows.append({'x0': l['x0'], 'y0': l['y0'], 'y1': l['y1'], 'spans': list(l['spans']), 'lines': [l]})
    body, aside = [], []
    for r in rows:
        finish(r)
        text = r['text']
        small = any(sp['size'] < 10 for sp in r['spans'])
        if r['y1'] < TOP and len(text) < 90 and (small or re.fullmatch(r'\d{1,4}', text) or re.match(r'^CAP\.', text, re.I)):
            aside.append(text)
            aside += [norm(sp['text']) for sp in r['spans'] if norm(sp['text'])]
        elif r['y0'] > BOTTOM and re.fullmatch(r'\d{1,4}', text):
            aside.append(text)
        else:
            body.append(r)
    return body, aside


def finish(r: dict) -> dict:
    if True:
        r['spans'].sort(key=lambda s: s['bbox'][0])
        text = norm(' '.join(s['text'] for s in r['spans']))
        # glue "(" "a" ")" split spans back together: spans are joined with a space only where the PDF has a gap
        parts = []
        for i, s in enumerate(r['spans']):
            if i and s['bbox'][0] - r['spans'][i - 1]['bbox'][2] > 1.0:
                parts.append(' ')
            parts.append(s['text'])
        text = norm(''.join(parts))
        r['text'] = text
        r['bold'] = all(s['flags'] & 16 for s in r['spans'] if s['text'].strip())
        r['first_bold'] = bool(r['spans'][0]['flags'] & 16)
        r['first'] = norm(r['spans'][0]['text'])
        r['size'] = max(s['size'] for s in r['spans'])
    return r


def stream_from(rows_all: list[dict], k: int) -> list[dict]:
    """Rows from index k on (a Schedule) taken apart into the lines the PDF draws, page by page in drawing order: a
    table is then read cell by cell (each cell's wrapped lines together), as the independent pdftotext -raw reading
    gives it, instead of row by row across the cells."""
    out = rows_all[:k + 1]
    by_page: dict[int, list] = {}
    for r in rows_all[k + 1:]:
        for l in r['lines']:
            by_page.setdefault(r['page'], []).append(l)
    for pg in sorted(by_page):
        for l in sorted(by_page[pg], key=lambda l: l['n']):
            r = finish({'x0': l['x0'], 'y0': l['y0'], 'y1': l['y1'], 'spans': list(l['spans']), 'lines': [l]})
            r['page'] = pg
            out.append(r)
    return out


def parse(path: Path) -> tuple[dict, dict]:
    doc = pymupdf.open(path)
    pages = [rows_of(p) for p in doc]
    cover = ' '.join(r['text'] for pg in pages[:2] for r in pg[0]) if pages else ''
    m = re.search(r'(?:Incorporating\s+all\s+amendments\s+up\s+to|Revised\s+up\s+to)\s+([^.]{6,40}?\d{4})', cover, re.I)
    upto = date_of(m.group(1)) if m else None
    # the body starts on the first page (after the arrangement) whose rows hold a bold section number or the long title
    start = None
    seen_arr = False
    for i, (rows, _) in enumerate(pages):
        txt = ' '.join(r['text'] for r in rows)
        if re.search(r'ARRANGEMENT\s+OF\s+SECTIONS', txt, re.I):
            seen_arr = True
            continue
        if not seen_arr:
            continue
        if any(re.match(r'^An?\s+(Ordinance|Enactment|Act)\b', r['text']) for r in rows) or \
                any(r['first_bold'] and SECNO.match(r['first']) for r in rows):
            start = i
            break
    if start is None:
        raise ValueError('body start not found')
    # end matter: the LIST OF AMENDMENTS table at the back is left out (and not read by the check either)
    end = len(pages)
    for i in range(start + 1, len(pages)):
        if any(re.fullmatch(r'\[?LIST\s+OF\s+AMENDMENTS\]?', r['text'], re.I) for r in pages[i][0]):
            end = i
            break
    # within the start page, drop the arrangement rows above the title block: the body starts at the last run of
    # bold rows before the long title (the title lines), else at the top
    rows_all: list[dict] = []
    aside: list[str] = []
    for i in range(start, end):
        for r in pages[i][0]:
            r['page'] = i
            rows_all.append(r)
        aside += pages[i][1]
    # Schedules (from the first schedule heading after a section) are read in drawing order
    if SCHEDULE_STREAM:
        seen_sec = False
        for k, r in enumerate(rows_all):
            if r['first_bold'] and SECNO.match(r['first']):
                seen_sec = True
            elif seen_sec and r['bold'] and len(r['text']) < 90 and SCHED.match(r['text']):
                rows_all = stream_from(rows_all, k)
                break
    # paragraphs
    paras: list[dict] = []
    gaps = sorted(b['y0'] - a['y1'] for a, b in zip(rows_all, rows_all[1:]) if a['page'] == b['page'])
    g = gaps[len(gaps) // 2] if gaps else 2.0
    xs = sorted(round(r['x0']) for r in rows_all)
    left = max(set(xs), key=xs.count) if xs else 0
    LABEL = re.compile(r'^(\(([a-z]{1,4}|[0-9]{1,3}[A-Z]{0,2}|[ivx]{1,6})\)|\[)')
    prev = None
    for r in rows_all:
        starts_sec = bool(r['first_bold'] and SECNO.match(r['first']))
        labelled = bool(LABEL.match(r['text'])) and r['x0'] > left + 15
        if prev is None:
            new = True
        elif r['page'] == prev['page']:
            new = (r['y0'] - prev['y1'] > g + 5) or r['bold'] != prev['bold'] or starts_sec or labelled                 or (STREAM_ROWS and r['y0'] < prev['y0'] - 1)  # the reading goes back up the page: the next cell
        else:
            # across a page break: a new paragraph if the row starts a section or a label, or the last row was a note
            new = starts_sec or r['bold'] != prev['bold'] or labelled or prev['text'].endswith(']')
        if new:
            paras.append({'text': r['text'], 'bold': r['bold'], 'sec': bool(r['first_bold'] and SECNO.match(r['first'])),
                          'num': (SECNO.match(r['first']) or [None, None])[1] if r['first_bold'] else None})
        else:
            paras[-1]['text'] = norm(paras[-1]['text'] + ' ' + r['text'])
        prev = r
    units: dict[str, dict] = {}
    order: list[str] = []
    cur = None
    buf: list[str] = []
    in_sched = False
    nsched = 0
    seen = {}

    def open_unit(key, label, kind, lines):
        nonlocal cur
        k = key
        n = 2
        while k in units:
            k = f'{key}-{n}'
            n += 1
        units[k] = {'label': label, 'kind': kind, 'lines': [f'# {label}'] + lines}
        order.append(k)
        cur = k

    title_lines: list[str] = []
    for i, p in enumerate(paras):
        nxt = paras[i + 1] if i + 1 < len(paras) else None
        if (p['bold'] or len(p['text']) < 40) and SCHED.match(p['text']) and cur is not None:
            in_sched = True
            nsched += 1
            open_unit(f'sch-{nsched:02d}', p['text'][:60].title() if len(p['text']) < 60 else f'Schedule {nsched}',
                      'schedule', buf + [p['text']])
            buf = []
            continue
        if not in_sched and p['sec'] and p['num']:
            num = p['num']
            mm = re.match(r'(\d+)([A-Z]*)', num)
            key = f'sec-{int(mm.group(1)):03d}' + (f'-{mm.group(2).lower()}' if mm.group(2) else '')
            open_unit(key, f'Section {num}', 'section', buf + [p['text']])
            buf = []
            continue
        if not in_sched and p['bold'] and nxt is not None and nxt['sec'] and cur is not None:
            buf.append(p['text'])  # the section's heading
            continue
        if not in_sched and p['bold'] and cur is not None:
            buf.append(p['text'])  # a Part or Chapter heading: stands above the next section
            continue
        if cur is None:
            if p['bold'] and nxt is not None and nxt['sec']:
                buf.append(p['text'])
                continue
            title_lines.append(p['text'])
            continue
        units[cur]['lines'] += buf + [p['text']]
        buf = []
    if buf and cur is not None:
        units[cur]['lines'] += buf
    out = {'000-title': {'label': 'Title', 'kind': 'title', 'text': '# Title\n' + '\n'.join(title_lines) + '\n'}}
    for k in order:
        u = units[k]
        out[k] = {'label': u['label'], 'kind': u['kind'], 'text': '\n'.join(u['lines']) + '\n'}
    meta = {'upto': upto, 'cover': cover, 'start_page': start, 'end_page': end, 'aside': aside,
            'sections': [k for k in order if k.startswith('sec-')], 'pages': len(doc)}
    return out, meta


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    u, m = parse(Path(sys.argv[1]))
    print({k: v for k, v in m.items() if k not in ('aside', 'cover')})
    for k, v in u.items():
        print('==', k)
        print(v['text'])
