"""Tests for the HTML, lex.uz, my.gov.uz and PDF parsers (saved NAMUNA fixtures)."""

from datetime import date
from pathlib import Path

from apps.collector.fetchers import FetchResult
from apps.collector.parsers import parse
from apps.collector.parsers.lexuz import parse_title

FIXTURES = Path(__file__).parent / "fixtures"


def _result(url: str, body: bytes, content_type: str = "text/html") -> FetchResult:
    """A 200 response for ``url``."""
    return FetchResult(url=url, final_url=url, status=200, content_type=content_type, body=body)


def namuna_pdf() -> bytes:
    """A minimal hand-written PDF with one line of text."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    stream = b"BT /F1 12 Tf 72 712 Td (NAMUNA PDF hujjat) Tj ET"
    objects.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer << /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objects) + 1, xref)
    return bytes(out)


def test_generic_html() -> None:
    """Chrome is dropped; headings, lists, tables and links survive."""
    html = (
        b"<html><head><title>NAMUNA sahifa</title></head><body><nav>Menu</nav>"
        b"<h2>Bo'lim</h2><p>Matn <b>qalin</b> bu.</p><ul><li>Bir</li><li>Ikki</li></ul>"
        b"<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
        b"<a href='/a#x'>a</a><a href='mailto:x@y.z'>m</a><a href='/a'>dup</a>"
        b"<script>alert(1)</script><footer>Pastki</footer></body></html>"
    )
    page = parse(_result("https://example.org/p", html))
    assert page.title == "NAMUNA sahifa"
    assert page.text == "## Bo'lim\n\nMatn qalin bu.\n\n- Bir\n\n- Ikki\n\nA | B\n1 | 2\n\namdup"
    assert page.links == ["https://example.org/a"]


def test_lexuz_page() -> None:
    """lex.uz: noise removed, part/chapter/article markers, metadata from the title only."""
    page = parse(
        _result("https://lex.uz/uz/docs/-1", (FIXTURES / "namuna_lexuz.html").read_bytes())
    )
    assert page.title == "NAMUNA qaror toʻgʻrisida"
    assert (page.section_label, page.published_at) == ("99-сон", date(2024, 2, 1))
    assert page.text == (
        "NAMUNA qaror toʻgʻrisida\n\n# I BOʻLIM. UMUMIY QOIDALAR\n\n## 1-bob. Asosiy qoidalar"
        "\n\n### 1-modda. NAMUNA maqsad\n\nNAMUNA birinchi band matni.\n\n### 2-modda. "
        "NAMUNA tartib\n\nNAMUNA ikkinchi band matni."
    )
    assert page.links == ["https://lex.uz/uz/docs/-123"]


def test_lexuz_title_without_number_and_missing_body() -> None:
    """Codes have no number; unknown titles stay as they are; no #divCont means no text."""
    assert parse_title("30.04.1998. NAMUNA kodeksi") == ("NAMUNA kodeksi", None, date(1998, 4, 30))
    assert parse_title("NAMUNA") == ("NAMUNA", None, None)
    page = parse(_result("https://lex.uz/uz/docs/-2", b"<title>NAMUNA</title><p>x</p>"))
    assert (page.title, page.text) == ("NAMUNA", "")


def test_mygov_service_page() -> None:
    """my.gov.uz: service title, accordion sections; ratings, buttons and chrome dropped."""
    body = (FIXTURES / "namuna_mygov.html").read_bytes()
    page = parse(_result("https://my.gov.uz/uz/service/1", body))
    assert page.title == "NAMUNA ID karta olish"
    assert page.text == (
        "## Xizmat narxi\n\n- NAMUNA boj miqdori\n\n## Kerakli hujjatlar\n\n"
        "NAMUNA pasport;\n\nNAMUNA ariza."
    )


def test_mygov_without_service_box_falls_back_to_title() -> None:
    """A page without the service box keeps its <title> and no text."""
    page = parse(_result("https://www.my.gov.uz/uz/x", b"<title>NAMUNA</title>"))
    assert (page.title, page.text) == ("NAMUNA", "")


def test_pdf() -> None:
    """PDFs are detected by type and parsed to text; title from the first line."""
    page = parse(_result("https://example.org/f.pdf", namuna_pdf(), "application/pdf"))
    assert page.text == "NAMUNA PDF hujjat"
    assert page.title == "NAMUNA PDF hujjat"
