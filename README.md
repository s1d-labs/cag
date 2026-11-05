# cag: CAG of India audit reports

A family of the s1d-labs scrape pool. It walks the report lists on cag.gov.in (state, Union, local bodies), reads each report page, and saves every PDF.

| Item | Stored |
|---|---|
| Report page | one record: title, summary, sector, date tabled, PDF links |
| PDF | the file in the bucket under `pdf/<report>/` and one record |

- Runs on GitHub runners, because the site answers from outside India: 3 workers, one request every 1.3 seconds.
- The site's filtered list for one state gave server errors on some days. This crawl uses the plain lists.

Setup: change `family.py`, then Actions -> setup. Tests: `python -m pytest tests`.
