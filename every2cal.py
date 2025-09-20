"""Command line utility to convert Everytime timetables into calendar files."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple, Union

from convert import Convert, Subject
from everytime import Everytime, EverytimeError

logger = logging.getLogger(__name__)

SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1
NO_EVENTS_EXIT_CODE = 2


def parse_arguments(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert an Everytime timetable to an iCalendar file.")
    parser.add_argument("--begin", type=str, required=True, help="Semester beginning date (YYYY-MM-DD).")
    parser.add_argument("--end", type=str, required=True, help="Semester ending date (YYYY-MM-DD).")
    parser.add_argument("--xml", type=Path, help="Path to a timetable XML file exported from Everytime.")
    parser.add_argument("--identifier", type=str, help="Everytime timetable identifier or sharing URL.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Location of the resulting .ics file. Defaults to /tmp/<identifier>.ics",
    )
    args = parser.parse_args(argv)
    if not args.identifier and not args.xml:
        parser.error("Either --identifier or --xml must be supplied.")

    return args


def _resolve_timetable_source(args: argparse.Namespace) -> Tuple[Union[str, Path], str]:
    if args.xml:
        xml_path = args.xml.expanduser()
        if not xml_path.exists():
            raise FileNotFoundError(f"The supplied XML file '{xml_path}' does not exist.")
        identifier = args.identifier or xml_path.stem
        return xml_path, identifier

    if not args.identifier:
        raise ValueError(
            "A timetable identifier is required when no XML file is provided. "
            "Pass --identifier with an Everytime URL or identifier."
        )

    client = Everytime(args.identifier)
    xml_data = client.get_timetable()
    return xml_data, client.identifier


def _create_calendar(
    xml_source: Union[str, Path],
    identifier: str,
    begin: str,
    end: str,
    output_path: Optional[Path],
) -> Optional[Path]:
    converter = Convert(xml_source)
    subjects: list[Subject] = converter.get_subjects()
    return converter.get_calendar(subjects, begin, end, identifier, output_path=output_path)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO)
    args = parse_arguments(argv)

    try:
        xml_source, identifier = _resolve_timetable_source(args)
        calendar_path = _create_calendar(
            xml_source,
            identifier,
            args.begin,
            args.end,
            args.output.expanduser() if args.output else None,
        )
    except (FileNotFoundError, ValueError, EverytimeError) as exc:
        logger.error("%s", exc)
        return ERROR_EXIT_CODE
    except Exception:  # pragma: no cover - safeguard for unexpected errors
        logger.exception("Unexpected error while creating calendar")
        return ERROR_EXIT_CODE

    if calendar_path is None:
        logger.warning("No events found in the timetable; no calendar file was created.")
        return NO_EVENTS_EXIT_CODE

    print(f"Calendar saved to {calendar_path}")
    return SUCCESS_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
