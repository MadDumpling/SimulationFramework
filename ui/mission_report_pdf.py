"""Build and export a printable spacecraft mission-screening report."""

from datetime import datetime, timezone
from pathlib import Path
import textwrap

from spacecraft.advisor import AdviceItem, format_advice
from spacecraft.analysis import MissionProfile, SpacecraftAnalysis
from spacecraft.mission import MissionSimulationResult
from spacecraft.vehicle import Spacecraft
from .mission_outcome import lunar_mission_report


def build_mission_report_text(
    spacecraft: Spacecraft,
    analysis: SpacecraftAnalysis,
    mission: MissionProfile,
    advice: list[AdviceItem],
    result: MissionSimulationResult | None = None,
) -> str:
    """Create the shared report text used by PDF export."""
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if result is None:
        mission_details = "\n".join(
            (
                "MISSION STATUS",
                "Trajectory has not been run; this is a preflight screening report.",
                f"Selected mission target: {mission.name}",
                f"Approximate target delta-v budget: {mission.required_delta_v / 1000.0:.2f} km/s",
                f"Estimated vehicle delta-v: {analysis.delta_v / 1000.0:.2f} km/s",
                f"Initial thrust-to-weight: {analysis.twr:.3f}",
                f"Power margin: {analysis.power_surplus_kw:+.2f} kW",
            )
        )
    else:
        mission_details = lunar_mission_report(result, analysis)

    return "\n".join(
        (
            "CELESTE SPACEWORKS — MISSION SCREENING REPORT",
            f"Vehicle: {spacecraft.name}",
            f"Generated: {generated}",
            f"Selected analysis target: {mission.name}",
            "",
            "This is an educational engineering-screening report, not flight certification.",
            "",
            mission_details,
            "",
            format_advice(advice),
        )
    )


def export_mission_report_pdf(path: str | Path, report_text: str) -> Path:
    """Write a paginated, searchable text PDF using only the standard library."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for line in report_text.splitlines():
        if not line:
            lines.append("")
            continue
        lines.extend(
            textwrap.wrap(
                line,
                width=100,
                subsequent_indent="   ",
                replace_whitespace=False,
                drop_whitespace=True,
                break_long_words=True,
            )
            or [""]
        )

    page_size = 48
    page_lines = [
        lines[start : start + page_size]
        for start in range(0, max(1, len(lines)), page_size)
    ]
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids ["
        + b" ".join(
            f"{4 + 2 * index} 0 R".encode("ascii")
            for index in range(len(page_lines))
        )
        + f"] /Count {len(page_lines)} >>".encode("ascii"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier "
        b"/Encoding /WinAnsiEncoding >>",
    ]
    for index, lines_on_page in enumerate(page_lines):
        page_id = 4 + 2 * index
        content_id = page_id + 1
        page = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")
        content = _pdf_text_stream(lines_on_page, index + 1)
        stream = (
            f"<< /Length {len(content)} >>\nstream\n".encode("ascii")
            + content
            + b"\nendstream"
        )
        objects.extend((page, stream))

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R "
            f"/Info << /Title (Celeste SpaceWorks Mission Screening Report) "
            f"/Author (Celeste SpaceWorks) >> >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    destination.write_bytes(pdf)
    return destination


def _pdf_text_stream(lines: list[str], page_number: int) -> bytes:
    commands = [
        "BT",
        "/F1 9 Tf",
        "50 810 Td",
        "(CELESTE SPACEWORKS - MISSION SCREENING REPORT) Tj",
        "0 -18 Td",
        f"(Page {page_number}) Tj",
        "0 -24 Td",
    ]
    for line in lines:
        commands.append(f"({_escape_pdf_text(line)}) Tj")
        commands.append("0 -14 Td")
    commands.append("ET")
    return "\n".join(commands).encode("ascii")


def _escape_pdf_text(text: str) -> str:
    encoded = text.encode("cp1252", errors="replace")
    escaped = []
    for byte in encoded:
        if byte in (ord("\\"), ord("("), ord(")")):
            escaped.append("\\" + chr(byte))
        elif 32 <= byte <= 126:
            escaped.append(chr(byte))
        else:
            escaped.append(f"\\{byte:03o}")
    return "".join(escaped)
