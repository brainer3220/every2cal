"""Utilities for turning Everytime timetables into iCalendar files."""
from __future__ import annotations

import datetime as dt
import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Union

from defusedxml import ElementTree

from dateutil import parser as date_parser
from icalendar import Calendar, Event

logger = logging.getLogger(__name__)

# The Everytime timetable expresses time as 5 minute slots.
_MINUTES_PER_SLOT = 5
_DEFAULT_OUTPUT_DIRECTORY = Path("/tmp")


@dataclass(frozen=True)
class MeetingTime:
    """Represents a single lecture/practice time for a subject."""

    weekday: int
    location: str
    start_time: dt.time
    end_time: dt.time


@dataclass(frozen=True)
class Subject:
    """Container for the metadata and meeting times of a subject."""

    name: str
    professor: str
    meetings: Sequence[MeetingTime]


class Convert:
    """Parse Everytime timetable XML data and write iCalendar files."""

    def __init__(self, xml_source: Union[str, Path]):
        """Initialise the converter with either raw XML or a file path."""

        self._xml_source = xml_source

    def get_subjects(self) -> List[Subject]:
        """Return the subjects parsed from the timetable XML."""

        root = self._load_xml_root()
        subjects: List[Subject] = []

        for subject_node in root.iter("subject"):
            name = self._get_attribute(subject_node.find("name"), "value")
            if not name:
                logger.debug("Skipping subject without a name: %s", ElementTree.tostring(subject_node))
                continue

            professor = self._get_attribute(subject_node.find("professor"), "value")
            time_node = subject_node.find("time")
            meetings = [self._parse_meeting(data_node) for data_node in time_node.findall("data")] if time_node else []

            subjects.append(Subject(name=name, professor=professor, meetings=meetings))

        return subjects

    def get_calendar(
        self,
        timetable: Sequence[Subject],
        start_date: str,
        end_date: str,
        identifier: str,
        *,
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """Create an iCalendar file from the supplied timetable."""

        if not timetable:
            logger.info("Timetable is empty; nothing to export.")
            return None

        calendar = Calendar()
        calendar.add("prodid", "-//Every2Cal//EN")
        calendar.add("version", "2.0")

        base_date = self._parse_date(start_date)
        until = date_parser.parse(end_date)

        for subject in timetable:
            for meeting in subject.meetings:
                event = Event()
                event.add("summary", subject.name)
                event.add("dtstart", self._combine_datetime(base_date, meeting.weekday, meeting.start_time))
                event.add("dtend", self._combine_datetime(base_date, meeting.weekday, meeting.end_time))
                event.add("rrule", {"freq": "WEEKLY", "until": until})
                if meeting.location:
                    event.add("location", meeting.location)
                if subject.professor:
                    event.add("description", subject.professor)
                calendar.add_component(event)

        has_events = any(True for _ in calendar.walk("VEVENT"))
        if not has_events:
            logger.warning("The timetable did not contain any meeting information.")
            return None

        destination = self._resolve_output_path(identifier, output_path)
        with destination.open("wb") as calendar_file:
            calendar_file.write(calendar.to_ical())

        logger.info("Created calendar at %s", destination)
        return destination

    def _load_xml_root(self) -> ElementTree.Element:
        """Load and return the root element of the timetable XML."""

        source = self._xml_source

        try:
            if isinstance(source, Path):
                return Convert._parse_xml_file(source)

            if isinstance(source, str):
                stripped = source.strip()
                # Attempt to parse as XML first so large payloads are handled without
                # being mistaken for filesystem paths.
                try:
                    return ElementTree.fromstring(stripped)
                except ElementTree.ParseError:
                    pass

                try:
                    potential_path = Path(stripped)
                except (OSError, TypeError):
                    potential_path = None
                else:
                    if potential_path and Convert._looks_like_path(stripped):
                        try:
                            if potential_path.exists():
                                return Convert._parse_xml_file(potential_path)
                        except OSError:
                            # Treat extremely long strings or invalid paths as raw XML content.
                            return ElementTree.fromstring(stripped)

                # Fallback to parsing the original source as XML to surface a clear error.
                return ElementTree.fromstring(stripped)

            return ElementTree.fromstring(str(source))
        except (OSError, ElementTree.ParseError, TypeError, ValueError) as exc:
            raise ValueError("Failed to parse timetable XML") from exc

    @staticmethod
    def _parse_xml_file(path: Path) -> ElementTree.Element:
        """Parse XML content from a filesystem path using defusedxml safeguards."""

        with path.open("rb") as xml_file:
            return ElementTree.parse(xml_file).getroot()

    @staticmethod
    def _looks_like_path(value: str) -> bool:
        """Heuristically determine whether the supplied string is a filesystem path."""

        if not value or value.startswith("<"):
            return False

        # XML payloads typically contain angle brackets or whitespace; ignore those.
        if any(char in value for char in "<>\n\r"):
            return False

        # Very long values are more likely to be XML content than an actual path.
        if len(value) > 512:
            return False

        return True

    @staticmethod
    def _get_attribute(element: Optional[ElementTree.Element], attribute: str, default: str = "") -> str:
        return default if element is None else element.get(attribute, default)

    def _parse_meeting(self, element: ElementTree.Element) -> MeetingTime:
        try:
            weekday = int(self._get_attribute(element, "day"))
        except ValueError as exc:
            raise ValueError("Invalid weekday value in timetable") from exc

        start_time = self._parse_time_slot(self._get_attribute(element, "starttime"))
        end_time = self._parse_time_slot(self._get_attribute(element, "endtime"))
        location = self._get_attribute(element, "place")

        return MeetingTime(weekday=weekday, location=location, start_time=start_time, end_time=end_time)

    @staticmethod
    def _parse_time_slot(value: str) -> dt.time:
        if not value:
            raise ValueError("Encountered an empty time slot value in timetable")
        try:
            total_minutes = int(value) * _MINUTES_PER_SLOT
        except ValueError as exc:
            raise ValueError("Time slot value is not an integer") from exc

        hours, minutes = divmod(total_minutes, 60)
        return dt.time(hour=hours, minute=minutes)

    @staticmethod
    def _parse_date(value: str) -> dt.date:
        try:
            parsed = date_parser.parse(value)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid date supplied; expected a parsable date string") from exc
        return parsed.date()

    @staticmethod
    def _combine_datetime(start_date: dt.date, target_weekday: int, time: dt.time) -> dt.datetime:
        if not 0 <= target_weekday <= 6:
            raise ValueError("Weekday must be between 0 (Monday) and 6 (Sunday)")

        base = Convert._next_weekday(start_date, target_weekday)
        return dt.datetime.combine(base, time)

    @staticmethod
    def _next_weekday(start_date: dt.date, target_weekday: int) -> dt.date:
        delta_days = (target_weekday - start_date.weekday()) % 7
        return start_date + dt.timedelta(days=delta_days)

    @staticmethod
    def _resolve_output_path(identifier: str, explicit_path: Optional[Path]) -> Path:
        if explicit_path is not None:
            destination = explicit_path.expanduser()
            destination.parent.mkdir(parents=True, exist_ok=True)
            return destination

        safe_identifier = Convert._sanitise_identifier(identifier)
        directory = _DEFAULT_OUTPUT_DIRECTORY
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{safe_identifier}.ics"

    @staticmethod
    def _sanitise_identifier(identifier: str) -> str:
        normalised = identifier.strip()
        cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", normalised)
        # Limit the filename prefix to keep the resulting path within sensible bounds.
        truncated = cleaned[:64].rstrip("._-") if cleaned else "timetable"
        hash_suffix = hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:8]
        return f"{truncated}_{hash_suffix}" if truncated else f"timetable_{hash_suffix}"
