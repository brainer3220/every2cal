"""CLI entry point for converting Everytime timetable into .ics."""

from __future__ import annotations

import argparse
from typing import Optional

import everytime
from convert import Convert


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Everytime timetable to .ics converter")
    parser.add_argument("--source", type=str, help="Path or Everytime URL/identifier", required=False)
    parser.add_argument("--begin", type=str, help="Semester beginning date (YYYYMMDD)", required=True)
    parser.add_argument("--end", type=str, help="Semester ending date (YYYYMMDD)", required=True)
    args = parser.parse_args(argv)

    if args.source:
        src = args.source
        e = everytime.Everytime(src)
        xml = e.get_timetable()
    else:
        # Expect XML to be piped via stdin or provided as file path; keep simple
        raise SystemExit("--source is required when using CLI")

    c = Convert(xml)
    # Use the identifier portion as file name if a URL was provided
    identifier = (args.source or "timetable").split("/")[-1]
    cal_path = c.get_calendar(c.get_subjects(), args.begin, args.end, identifier)
    if not cal_path:
        print("No events found.")
        return 1
    print(f"Generated: {cal_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
