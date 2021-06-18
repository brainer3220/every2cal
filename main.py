from opyrator.components.types import FileContent
from pydantic import BaseModel, Field
from convert import Convert


class Input(BaseModel):
    xml: str = Field(
        title="XML을 넣어주세요."
    )

    begin_date: int = Field(
        title="""학기 시작일을 넣어주세요.
        예) 2021년 03월 02일 == 20210302""",
        ge=20000000
        # le=21000000
    )

    end_date: int = Field(
        title="""학기 마지막일을 넣어 주세요.
        예) 2021년 06월 21일 == 20210621""",
        ge=20000000
        # le=21000000
    )


class Output(BaseModel):
    iCal: FileContent = Field(
        mime_type="schedule.ics",
        description="ical file.",
    )


def hello_world(input: Input) -> Output:
    """Returns ics file"""

    c = Convert(input.xml)
    ical = c.get_calendar(c.get_subjects(), str(input.begin_date), str(input.end_date))

    return Output(iCal=ical)

