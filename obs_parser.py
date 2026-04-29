"""
OBS PDF/bilde parsing med Claude vision.

Denne modulen håndterer parsing av OBS-kundeaviser (PDF/bilde) 
ved hjelp av Claude AI vision-modell.

Bruk:
    result = parse_obs_image("path/to/image.jpg")
    # eller
    result = parse_obs_pdf("path/to/catalog.pdf")
"""

import base64
import json
import re
from pathlib import Path
from datetime import date, timedelta
from typing import Optional


def _read_image_as_base64(image_path: str) -> str:
    """Les bilde og konverter til base64 for Claude vision."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def _extract_date_from_filename(filename: str) -> Optional[tuple[str, str]]:
    """
    Prøv å ekstrahère valid_from og valid_to fra filnavn.
    F.eks. "kundeavis_uke_18_2026.pdf" → ("2026-04-28", "2026-05-04")
    """
    match = re.search(r"uke[_\s]*(\d+)[_\s]*(\d{4})", filename, re.IGNORECASE)
    if not match:
        return None

    week_num = int(match.group(1))
    year = int(match.group(2))

    # ISO week → dato
    jan_4 = date(year, 1, 4)
    week_one_monday = jan_4 - timedelta(days=jan_4.weekday())
    monday = week_one_monday + timedelta(weeks=week_num - 1)
    sunday = monday + timedelta(days=6)

    return monday.isoformat(), sunday.isoformat()


def parse_obs_image(
    image_path: str,
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    source_label: Optional[str] = None,
) -> dict:
    """
    Parse OBS-kundeavis bilde med Claude vision.

    Args:
        image_path: Sti til bilde (JPG, PNG, etc)
        valid_from: YYYY-MM-DD (hvis ikke oppgitt, prøves å ekstraheres fra filnavn)
        valid_to: YYYY-MM-DD (hvis ikke oppgitt, beregnes fra valid_from)
        source_label: Kildemerke (f.eks. "obs_uke_18_vinterbro")

    Returns:
        {
            "items": [
                {
                    "product_name": "...",
                    "brand": "...",
                    "volume": "...",
                    "price": XX.XX,
                    "normal_price": XX.XX or None
                },
                ...
            ],
            "valid_from": "2026-04-28",
            "valid_to": "2026-05-04",
            "source": "..."
        }
    """
    # Forsøk å ekstrahère datoer fra filnavn
    if valid_from is None or valid_to is None:
        extracted = _extract_date_from_filename(Path(image_path).name)
        if extracted:
            valid_from, valid_to = extracted

    if valid_from is None:
        valid_from = date.today().isoformat()
    if valid_to is None:
        valid_to = (date.fromisoformat(valid_from) + timedelta(days=6)).isoformat()

    if source_label is None:
        source_label = f"obs_{Path(image_path).stem}"

    # TODO: Implementer Claude vision API-kall her
    # For nå: returner tomme resultater
    return {
        "items": [],
        "valid_from": valid_from,
        "valid_to": valid_to,
        "source": source_label,
        "status": "not_implemented",
        "message": "Claude vision API kreves. Se obs_import.md for manual workflow.",
    }


def parse_obs_pdf(
    pdf_path: str,
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    source_label: Optional[str] = None,
) -> dict:
    """
    Parse OBS-PDF med Claude vision.

    Args:
        pdf_path: Sti til PDF-fil
        valid_from: YYYY-MM-DD
        valid_to: YYYY-MM-DD
        source_label: Kildemerke

    Returns:
        Se parse_obs_image() for returformat.

    Note:
        Denne implementasjonen krever Claude API + pdf2image/pypdf.
        For nå: bruk parse_obs_image() med screenshot av PDF.
    """
    # TODO: pdf → images → parse_obs_image()
    return {
        "items": [],
        "valid_from": valid_from or date.today().isoformat(),
        "valid_to": valid_to,
        "status": "not_implemented",
        "message": "PDF parsing krever pdf2image. Konverter til JPG først.",
    }


def format_for_mcp_import(parse_result: dict) -> dict:
    """
    Formatér parse_result() til format som import_obs_catalog tool forventer.

    Brukes som bridge mellom lokal parsing og MCP-tool.
    """
    return {
        "items": parse_result.get("items", []),
        "valid_from": parse_result.get("valid_from"),
        "valid_to": parse_result.get("valid_to"),
        "source_label": parse_result.get("source"),
    }
