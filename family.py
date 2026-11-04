"""What this family scrapes: every audit report on cag.gov.in. The list pages give report pages, which give PDFs. All three go through one queue."""
import json
from pathlib import Path

FAMILY = json.loads((Path(__file__).parent / "scrape.json").read_text())["family"]
HOST = "cag.gov.in"
# report groups on the site: state, Union, local bodies
GROUPS = {"state": 49, "union": 50, "local": 51}
PROJECTS = [{"name": f"{FAMILY}-reports", "title": "CAG audit reports", "task": "crawl", "unit_label": "page or file", "record_label": "report or PDF",
             "items": [{"key": f"list-{g}-1", "payload": {"type": "list", "group": g, "gt": n, "page": 1}} for g, n in GROUPS.items()]}]
PROBES = [{"name": f"{FAMILY}:{HOST}", "url": f"https://{HOST}/en/audit-report", "expect": "audit"}]
