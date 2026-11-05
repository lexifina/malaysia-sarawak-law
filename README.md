# Sarawak: law history in git

The Ordinances of the State of Sarawak (Malaysia) as a git history: one file per section, one paragraph per line, so `git blame`, `git log` and `git diff` work line by line. The text is the English text of the State Attorney-General's Chambers' online reprints on Sarawak LawNet.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law).

## What this repository holds

**Current text only, not yet a history.** Sarawak LawNet publishes online reprints of updated Ordinance text, with no earlier consolidated text for these records. Most reprints state on the cover the date through which amendments are incorporated. Public Parks and Greens Ordinance, 1993 and Sarawak Rivers Ordinance, 1993 instead state the in-force date of their latest amendment in the final List of Amendments. Each Ordinance has one commit holding that reprint's text, credited to the State Attorney-General's Chambers ("oldest version available"), not to an amending law.

| Folder | What |
| --- | --- |
| one folder per Ordinance (by its short title, e.g. `advocates-ordinance-1953/`) | the Ordinance as reprinted: `000-title.md`, one file per section, one per Schedule |

The Ordinances are added in parts in the order of LawNet's full listing. Subsidiary legislation is not included. An Ordinance is left out until its text can be read reliably and its current version can be dated from the source. This includes reprints whose Schedules hold tables or forms the independent check below does not find in the same order, and reprints with neither a cover amendment date nor a dated final List of Amendments entry.

## Source

[Sarawak LawNet](https://lawnet.sarawak.gov.my/lawnet/Law/TLnetPubHome.jsp), "the official Sarawak Government website for Statutes of Sarawak", provided and maintained by the Sarawak State Attorney-General's Chambers: the "Laws of Sarawak" online reprints (PDF). Each PDF's sha256 is recorded with its version in `data/versions.json`.

## Dates

For most Ordinances, the version date is the day the reprint's cover says amendments are incorporated up to. That is the day the consolidation reaches, not necessarily the day of the last amendment. Public Parks and Greens Ordinance, 1993 is dated 1 January 2004 and Sarawak Rivers Ordinance, 1993 is dated 1 January 2007: their reprints' final List of Amendments gives those dates as the in-force dates of their latest amendments. Version times are noon in Kuching.

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
