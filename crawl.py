"""One queue item: a list page, a report page or a PDF."""
import hashlib
import os
import signal
import sys
import time
from urllib.parse import quote

import requests
from scrape_hub_client import HubClient, seed_queue

from parse import list_page, list_url, pdf_key, report_page

PROJECT = os.environ["SCRAPE_POOL_PROJECT"]
DEADLINE = time.time() + float(os.environ.get("SCRAPE_MAX_HOURS", "1")) * 3600 - 120
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; s1d-labs public records crawl; +https://labs.s1d.me)"}
stop = False


def on_signal(*_):
    global stop
    stop = True


def get(hub, s, url):
    t = time.time()
    try:
        r = s.get(url, timeout=(20, 300))
    except requests.RequestException:
        hub.metric("http_error")
        hub.error()
        return None
    hub.metric("n_http")
    hub.metric("t_http_s", time.time() - t)
    if r.status_code != 200:
        hub.metric(f"http_{r.status_code}")
        if r.status_code in (403, 429, 503):
            hub.block()
        return None
    return r


def work(hub, s, key, p):
    if p["type"] == "list":
        r = get(hub, s, list_url(p["gt"], p["page"]))
        if r is None:
            return None
        found, last = list_page(r.text)
        if p["page"] == 1 and last > 1:
            seed_queue(PROJECT, [{"key": f"list-{p['group']}-{n}", "payload": {**p, "page": n}} for n in range(2, last + 1)])
        for x in found:
            hub.record(f"report-{x['id']}", {"type": "report", "group": p["group"], **x})       # the report page replaces this with the full record
        seed_queue(PROJECT, [{"key": f"report-{x['id']}", "payload": {"type": "report", "group": p["group"], **x}} for x in found])
        return len(found)
    if p["type"] == "report":
        r = get(hub, s, f"https://cag.gov.in/en/audit-report/details/{p['id']}")
        if r is None:
            return None
        pdfs, tabled = report_page(r.text)
        hub.record(f"report-{p['id']}", {"type": "report", "id": p["id"], "group": p["group"], "title": p["title"], "blurb": p["blurb"], "sector": p["sector"], "tabled": tabled, "pdfs": [{"url": u, "label": l} for u, l in pdfs.items()]})
        if pdfs:
            seed_queue(PROJECT, [{"key": pdf_key(u), "payload": {"type": "pdf", "report": p["id"], "url": u, "label": l}} for u, l in pdfs.items()])
        return 1
    r = get(hub, s, quote(p["url"], safe=":/%?=&+"))
    if r is None or not r.content.startswith(b"%PDF"):
        return None
    sha = hashlib.sha256(r.content).hexdigest()
    path = f"pdf/{p['report']}/{sha[:16]}.pdf"
    hub.upload_many([(path, r.content, "application/pdf")])
    hub.record(key, {"type": "pdf", "report": p["report"], "url": p["url"], "label": p["label"], "file": path, "bytes": len(r.content), "sha256": sha})
    return 1


def main():
    hub = HubClient(PROJECT, job_index=int(os.environ.get("SCRAPE_JOB_INDEX", 0)), total_jobs=int(os.environ.get("SCRAPE_TOTAL_JOBS", 1)))
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    s = requests.Session()
    s.headers.update(HEADERS)
    while time.time() < DEADLINE and not stop:
        if hub.settings.get("paused"):
            time.sleep(30)
            continue
        items = hub.claim(1, steal=True, retry_failed=True)
        if not items:
            break
        it = items[0]
        n = work(hub, s, it["key"], it["payload"])
        if n is None:
            hub.complete([it["key"]], "failed", error="no page")
        else:
            hub.complete([it["key"]], "done", fetched=n)
        time.sleep(max(1, hub.settings.get("delay_ms", 0) / 1000))
    hub.close("finished" if not stop else "failed", "" if not stop else "stopped by signal")


if __name__ == "__main__":
    sys.exit(main())
