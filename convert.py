"""Utilities to convert Everytime timetable XML into an iCalendar (.ics) file."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import datetime as dt
import xml.etree.ElementTree as ET

from dateutil import parser as dtparse
from icalendar import Calendar, Event

logger = logging.getLogger(__name__)


class Convert:
    """Convert timetable XML to subjects and calendar.

    The class accepts either a path to an XML file or an XML string.
    """

    def __init__(self, xml_or_path: str) -> None:
        self._xml_or_path = xml_or_path

    def _get_root(self) -> ET.Element:
        """Return the root element of the XML.

        Tries to resolve input as a filesystem path first when it exists; otherwise
        treats it as an XML string.
        """
        candidate = Path(self._xml_or_path)
        if candidate.exists():
            logger.debug("Parsing timetable from file: %s", candidate)
            tree = ET.parse(candidate)
            return tree.getroot()

        logger.debug("Parsing timetable from XML string (%d chars)", len(self._xml_or_path))
        return ET.fromstring(self._xml_or_path)

    def get_subjects(self) -> List[Dict[str, Any]]:
        """Parse XML and return a normalized list of subjects.

        Returns a list of dicts with keys: name, professor, info[].
        """
        result: List[Dict[str, Any]] = []
        root = self._get_root()

        for subject in root.iter("subject"):
            name_attr = subject.find("name")
            professor_attr = subject.find("professor")
            if name_attr is None or professor_attr is None:
                logger.debug("Skipping subject missing name/professor")
                continue

            def _slot(x: ET.Element) -> Dict[str, str]:
                start_raw = int(x.get("starttime", "0"))
                end_raw = int(x.get("endtime", "0"))
                # Each unit is 5 minutes; convert to HH:MM
                start_at = "{:02d}:{:02d}".format(*divmod(start_raw * 5, 60))
                end_at = "{:02d}:{:02d}".format(*divmod(end_raw * 5, 60))
                return {
                    "day": x.get("day", "0"),
                    "place": x.get("place", ""),
                    "startAt": start_at,
                    "endAt": end_at,
                }

            time_node = subject.find("time")
            times = [] if time_node is None else list(map(_slot, time_node.findall("data")))

            single_subject = {
                "name": name_attr.get("value", ""),
                "professor": professor_attr.get("value", ""),
                "info": times,
            }
            result.append(single_subject)

        return result

    def get_calendar(
        self,
        timetable: Iterable[Dict[str, Any]],
        start_date: str,
        end_date: str,
        identifier: str,
    ) -> Optional[str]:
        """Create a weekly-recurring calendar between start_date and end_date.

        Returns the file path to the generated .ics on success, otherwise None
        when there are no events.
        """
        cal = Calendar()
        event_count = 0

        for item in timetable:
            for time in item.get("info", []):
                event = Event()
                event.add("summary", item.get("name", ""))
                start_dt = dtparse.parse(f"{self.get_nearest_date(start_date, time.get('day', '0'))} {time.get('startAt', '00:00')}")
                end_dt = dtparse.parse(f"{self.get_nearest_date(start_date, time.get('day', '0'))} {time.get('endAt', '00:00')}")
                event.add("dtstart", start_dt)
                event.add("dtend", end_dt)
                event.add("rrule", {"freq": "WEEKLY", "until": dtparse.parse(end_date)})
                place = time.get("place")
                if place:
                    event.add("location", place)
                cal.add_component(event)
                event_count += 1

        if event_count == 0:
            logger.warning("No events found in timetable; skipping file generation.")
            return None

        out_path = Path("/tmp") / f"{identifier}.ics"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as f:
            f.write(cal.to_ical())
        logger.info("Calendar generated: %s (%d events)", out_path, event_count)
        return str(out_path)

    def get_nearest_date(self, start_date: str, weekday: str | int) -> dt.date:
        """Return the first date on/after start_date that matches weekday (0=Mon)."""
        start = dtparse.parse(start_date).date()
        wd = int(weekday)
        delta = (wd - start.weekday()) % 7
        return start + dt.timedelta(days=delta)
