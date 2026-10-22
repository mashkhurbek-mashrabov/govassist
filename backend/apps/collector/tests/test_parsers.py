"""Tests for HTML, PDF, and lex.uz parsers."""

from datetime import date
from pathlib import Path

import pytest

from apps.collector.fetchers import FetchResult
from apps.collector.models import CrawlSource
from apps.collector.parsers import parse, parse_html, parse_lexuz, parse_pdf

FIXTURES_DIR = Path(__file__).parent / "fixtures"
NAMUNA_SERVICE_HTML = (FIXTURES_DIR / "namuna_service.html").read_bytes()
NAMUNA_LEXUZ_HTML = (FIXTURES_DIR / "namuna_lexuz.html").read_bytes()


def _make_namuna_pdf() -> bytes:
    """Build a minimal valid PDF (< 20KB) containing text for testing."""
    lines = [
        b"%PDF-1.4",
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj"
        ),
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        b"5 0 obj << /Length 55 >> stream",
        b"BT",
        b"/F1 12 Tf",
        b"72 712 Td",
        b"(NAMUNA Test Document) Tj",
        b"ET",
        b"endstream",
        b"endobj",
        b"xref",
        b"0 6",
        b"0000000000 65535 f\r",
        b"0000000009 00000 n\r",
        b"0000000058 00000 n\r",
        b"0000000115 00000 n\r",
        b"0000000244 00000 n\r",
        b"0000000318 00000 n\r",
        b"trailer << /Size 6 /Root 1 0 R >>",
        b"startxref",
        b"424",
        b"%%EOF",
    ]
    return b"\n".join(lines)


def test_parse_html_structure_and_links() -> None:
    """Verifies headings, lists, tables, link resolution, and tag dropping."""
    res = FetchResult(
        url="https://my.gov.uz/uz/service/id-card",
        final_url="https://my.gov.uz/uz/service/id-card",
        status=200,
        content_type="text/html",
        body=NAMUNA_SERVICE_HTML,
    )
    parsed = parse_html(res)

    # Title extraction
    assert parsed.title == "NAMUNA ID-karta olish xizmati"

    # Drop checks: nav and footer text should not appear
    assert "Bosh sahifa" not in parsed.text
    assert "Barcha huquqlar himoyalangan" not in parsed.text

    # Markdown elements: h1, h2, li, table
    assert "# NAMUNA ID-karta olish xizmati" in parsed.text
    assert "## Kerakli hujjatlar" in parsed.text
    assert "- Ariza" in parsed.text
    assert "- Tugʻilganlik haqida guvohnoma" in parsed.text
    assert "Xizmat turi | Toʻlov miqdori" in parsed.text
    assert "Birinchi marta olish | BHMning 89 foizi" in parsed.text

    # Links resolved to absolute
    assert "https://my.gov.uz/offices/centers" in parsed.links


def test_parse_pdf() -> None:
    """Verifies text and title extraction from PDF."""
    res = FetchResult(
        url="https://example.uz/docs/namuna_guide.pdf",
        final_url="https://example.uz/docs/namuna_guide.pdf",
        status=200,
        content_type="application/pdf",
        body=_make_namuna_pdf(),
    )
    parsed = parse_pdf(res)

    assert "NAMUNA Test Document" in parsed.text
    assert parsed.title == "NAMUNA Test Document"
    assert parsed.links == []
    assert parsed.published_at is None
    assert parsed.section_label is None


def test_parse_lexuz() -> None:
    """Verifies article markers (###), chapter markers (##), act number, and date."""
    res = FetchResult(
        url="https://lex.uz/docs/850",
        final_url="https://lex.uz/docs/850",
        status=200,
        content_type="text/html",
        body=NAMUNA_LEXUZ_HTML,
    )
    parsed = parse_lexuz(res)

    assert "## 1-bob. Umumiy qoidalar" in parsed.text
    assert "### 1-modda. Ushbu Qonunning maqsadi" in parsed.text
    assert "### 2-modda. Asosiy tushunchalar" in parsed.text

    # Act number and date
    assert parsed.section_label == "OʻRQ-850"
    assert parsed.published_at == date(2024, 3, 15)


def test_parse_lexuz_missing_metadata() -> None:
    """Verifies lexuz parser never invents missing act number or date."""
    html_without_meta = b"<html><body><p>NAMUNA text without act number or date</p></body></html>"
    res = FetchResult(
        url="https://lex.uz/docs/empty",
        final_url="https://lex.uz/docs/empty",
        status=200,
        content_type="text/html",
        body=html_without_meta,
    )
    parsed = parse_lexuz(res)
    assert parsed.section_label is None
    assert parsed.published_at is None


@pytest.mark.django_db
def test_parse_dispatcher_selection() -> None:
    """Verifies dispatcher picks proper parser according to content type and host."""
    source_mygov = CrawlSource(
        name="mygov",
        start_url="https://my.gov.uz/services",
    )
    source_lexuz = CrawlSource(
        name="lexuz",
        start_url="https://lex.uz/acts",
    )

    pdf_res = FetchResult(
        url="https://my.gov.uz/file.pdf",
        final_url="https://my.gov.uz/file.pdf",
        status=200,
        content_type="application/pdf",
        body=_make_namuna_pdf(),
    )
    parsed_pdf = parse(pdf_res, source_mygov)
    assert "NAMUNA Test Document" in parsed_pdf.text

    lex_res = FetchResult(
        url="https://lex.uz/docs/850",
        final_url="https://lex.uz/docs/850",
        status=200,
        content_type="text/html",
        body=NAMUNA_LEXUZ_HTML,
    )
    parsed_lex = parse(lex_res, source_lexuz)
    assert parsed_lex.section_label == "OʻRQ-850"

    html_res = FetchResult(
        url="https://my.gov.uz/service",
        final_url="https://my.gov.uz/service",
        status=200,
        content_type="text/html",
        body=NAMUNA_SERVICE_HTML,
    )
    parsed_html = parse(html_res, source_mygov)
    assert parsed_html.title == "NAMUNA ID-karta olish xizmati"
