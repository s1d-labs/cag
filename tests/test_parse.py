from pathlib import Path

from parse import list_page, list_url, pdf_key, report_page

PAGES = Path(__file__).parent / "pages"


def test_list():
    found, last = list_page((PAGES / "list.html").read_text(errors="replace"))
    assert found and found[0]["id"].isdigit() and found[0]["title"] and last >= 1


def test_report():
    pdfs, _ = report_page((PAGES / "report.html").read_text(errors="replace"))
    assert pdfs and all(u.startswith("https://") for u in pdfs)


def test_small():
    assert "gt=49&page=2" in list_url(49, 2) and pdf_key("a").startswith("pdf-")
