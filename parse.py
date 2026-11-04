"""Pure functions on cag.gov.in pages."""
import hashlib
import html
import re


def text(s):
    return html.unescape(re.sub(r"<[^>]+>|\s+", " ", s)).strip()


def list_url(gt, page):
    return f"https://cag.gov.in/en/audit-report?gt={gt}&page={page}"


def list_page(h):
    """-> ([{id, title, blurb, sector}], last page number)"""
    out = []
    for block in re.split(r'class="reportDetail"', h)[1:]:
        m = re.search(r'<a href="/en/audit-report/details/(\d+)">\s*([^<]+)', block)
        if m:
            d = re.search(r"<p>(.*?)</p>", block, re.S)
            s = re.search(r"Sector:</div>(.*?)</div>\s*</div>", block, re.S)
            out.append({"id": m.group(1), "title": html.unescape(m.group(2)).strip(), "blurb": text(d.group(1)) if d else "", "sector": text(s.group(1)) if s else ""})
    pages = [int(x) for x in re.findall(r"page=(\d+)", h)]
    return out, max(pages) if pages else 1


def report_page(h):
    """-> ({url: label} of every PDF, date tabled). English and Hindi both."""
    u = {}
    for m in re.finditer(r'<a\b[^>]*href="(https://[^"]*?/uploads/download_audit_report/[^"]+)"[^>]*>(.*?)</a>', h, re.S):
        url, label = html.unescape(m.group(1)), text(m.group(2))
        if url not in u or len(label) > len(u[url]):
            u[url] = label
    t = re.search(r"Date on which Report Tabled:\s*</?[^>]*>?\s*([^<]+)", h)
    return u, t.group(1).strip() if t else ""


def pdf_key(url):
    return "pdf-" + hashlib.sha1(url.encode()).hexdigest()[:24]
