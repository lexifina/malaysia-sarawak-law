# Sarawak: law history in git

The Ordinances of the State of Sarawak (Malaysia) as a git history: one file per section, one paragraph per line, so `git blame`, `git log` and `git diff` work line by line. The text is the English text of the State Attorney-General's Chambers' online reprints on Sarawak LawNet.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law).

## What this repository holds

**Current text only, not yet a history.** Sarawak LawNet publishes each Ordinance as an online version of the updated text of its reprint, "incorporating all amendments up to" a stated date, with no earlier consolidated text. So each Ordinance is one commit holding its whole text as of that date, credited to the State Attorney-General's Chambers ("oldest version available"), not to an amending law.

| Folder | What |
| --- | --- |
| one folder per Ordinance (by its short title, e.g. `advocates-ordinance-1953/`) | the Ordinance as reprinted: `000-title.md`, one file per section, one per Schedule |

The Ordinances are added in parts of about fifty, in the order of LawNet's full listing. Subsidiary legislation is not included. An Ordinance is left out until it can be read reliably: reprints whose Schedules hold tables or forms the independent check below does not find in the same order, and reprints whose cover gives no "amendments up to" date.

## Source

[Sarawak LawNet](https://lawnet.sarawak.gov.my/lawnet/Law/TLnetPubHome.jsp), "the official Sarawak Government website for Statutes of Sarawak", provided and maintained by the Sarawak State Attorney-General's Chambers: the "Laws of Sarawak" online reprints (PDF). Each PDF's sha256 is recorded with its version in `data/versions.json`.

## Dates

Each Ordinance's version is dated by the day its reprint's cover says amendments are incorporated up to, at noon in Kuching. That is the day the consolidation reaches, not the day of the last amendment.

## How it is built

Lexifina reads the sources listed here and records each act's dated versions, and the laws that made each change, in one corpus file. `tools/build.py` writes this repository from that file, and the same corpus always gives the same commit hashes; `REPRODUCE.md` gives the details and the checks. A model (Claude) wrote Lexifina's code; it wrote no legal text, and no model runs when the history is built.

The text layer of each PDF (no OCR) becomes one file per section. The cover, the revision page, the arrangement of sections, running heads, page numbers and the "List of Amendments" tables at the back are left out. The amendment notes printed under provisions ("[Am. Ord. No. 3/60.]") stay as printed. Part and Chapter headings stand above the first section under them; each section's heading is the line before its text.

## How it is checked

Every version is read back from git on the day it took effect and must match the corpus. A second, independent reading of every PDF (a different PDF engine) must contain every letter and digit of each Ordinance in the same order, with nothing in the body left out. Results are in `REPRODUCE.md`.

## What "author" means

The author of each commit is the publisher (the State Attorney-General's Chambers, Sarawak), with an e-mail address that cannot exist; the committer is always Lexifina.

## Limits

Only the text as of each reprint's date is here: no earlier versions, and not the Ordinances as enacted. LawNet's own notice: "A print out from this System is not a copy of the State Government Gazette printed by the State Government Printer. For the purpose of any legal proceeding, authoritative copy of the law as printed by the State Government Printer should be used."

## Licence

See [LICENSE](LICENSE): official texts of a legislative nature are excluded from copyright by the Copyright Act 1987 [Act 332], s. 3. Source: State Attorney-General's Chambers, Sarawak (Sarawak LawNet).
