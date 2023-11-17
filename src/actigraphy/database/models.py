"""Database models for the actigraphy database."""
import datetime

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import hybrid

from actigraphy.database import database


class BaseTable(database.Base):  # type: ignore[misc]
    """Basic settings of a table. Contains an id, time_created, and time_updated."""

    __abstract__ = True

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, autoincrement=True)  # noqa: A003
    time_created: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        server_default=sqlalchemy.func.now(),
    )
    time_updated: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    )


class SleepTime(BaseTable):
    """Represents a sleep time record in the database.

    Attributes:
        id: The unique identifier of the sleep time record.
        onset: The date and time when the sleep started.
        onset_utc_offset: The UTC offset of the onset in seconds.
        wakeup: The date and time when the sleep ended.
        wakeup_utc_offset: The UTC offset of the wakeup in seconds.
        day: The day when the sleep occurred.
    """

    __tablename__ = "sleep_times"

    onset: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime,
        nullable=False,
    )
    onset_utc_offset: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.Integer,
        nullable=False,
    )
    wakeup: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime,
        nullable=False,
    )
    wakeup_utc_offset: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.Integer,
        nullable=False,
    )
    day_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("days.id"),
        nullable=False,
    )

    day = orm.relationship("Day", back_populates="sleep_times")

    @hybrid.hybrid_property
    def onset_with_tz(self) -> datetime.datetime:
        """Returns the onset time of the event with the timezone information added.

        Returns:
            datetime.datetime: The onset time with timezone information.
        """
        onset_utc = self.onset.replace(tzinfo=datetime.UTC)
        return onset_utc.astimezone(
            datetime.timezone(datetime.timedelta(seconds=self.onset_utc_offset)),
        )

    @hybrid.hybrid_property
    def wakeup_with_tz(self) -> datetime.datetime:
        """Returns the wakeup time of the event with the timezone information added.

        Returns:
            datetime.datetime: The wakeup time with timezone information.
        """
        wakeup_utc = self.wakeup.replace(tzinfo=datetime.UTC)
        return wakeup_utc.astimezone(
            datetime.timezone(datetime.timedelta(seconds=self.onset_utc_offset)),
        )


class Day(BaseTable):
    """A class representing a day in the database.

    Combinations of subjects and dates must be unique.

    Attributes:
        date: The date of the day.
        is_missing_sleep: Whether the day is missing sleep data.
        is_multiple_sleep: Whether the day has multiple sleep periods.
        is_reviewed: Whether the day has been reviewed.
        subject: The subject to which the day belongs.
        sleep_times: The sleep times associated with the day.
    """

    __tablename__ = "days"
    __table_args__ = (
        sqlalchemy.UniqueConstraint("subject_id", "date", name="uq_subject_date"),
    )

    date: orm.Mapped[datetime.date] = orm.mapped_column(
        sqlalchemy.Date,
        nullable=False,
    )
    is_missing_sleep: orm.Mapped[bool] = orm.mapped_column(
        sqlalchemy.Boolean,
        default=False,
    )
    is_multiple_sleep: orm.Mapped[bool] = orm.mapped_column(
        sqlalchemy.Boolean,
        default=False,
    )
    is_reviewed: orm.Mapped[bool] = orm.mapped_column(
        sqlalchemy.Boolean,
        default=False,
    )
    subject_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("subjects.id"),
        nullable=False,
    )

    subject = orm.relationship(
        "Subject",
        back_populates="days",
    )
    sleep_times = orm.relationship(
        "SleepTime",
        back_populates="day",
        cascade="all, delete",
    )


class Subject(BaseTable):
    """A class representing a subject in the actigraphy database.

    Attributes:
        is_finished: Whether the subject has finished the study or not.
        days: A list of Day objects associated with the subject.
    """

    __tablename__ = "subjects"

    name: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String(128),
        nullable=False,
        unique=True,
    )
    n_points_per_day: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.Integer,
        nullable=False,
    )
    is_finished: orm.Mapped[bool] = orm.mapped_column(
        sqlalchemy.Boolean,
        default=False,
    )

    days = orm.relationship(
        "Day",
        back_populates="subject",
        cascade="all, delete",
    )
