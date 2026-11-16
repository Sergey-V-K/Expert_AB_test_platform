"""Data sources. Every source returns the same thing: summary stats per group.

The engine and the UI do not care where the data comes from.

v1: only manual input works. Other sources are stubs: the UI shows them
as disabled ("coming soon"). See BACKLOG B4, B5, B7.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class GroupStats:
    """Summary stats for one group. Per-user level: one user = one row.

    Binary metric: fill `conversions`.
    Continuous metric: fill `mean` and `sd`.
    """

    n: int
    conversions: Optional[int] = None
    mean: Optional[float] = None
    sd: Optional[float] = None


@dataclass(frozen=True)
class ExperimentData:
    metric_type: str      # "binary" or "continuous"
    control: GroupStats
    treatment: GroupStats


class DataSource(Protocol):
    """Interface for all sources."""

    name: str
    available: bool  # False -> UI shows the source as disabled

    def load(self) -> ExperimentData:
        """Return summary stats for control and treatment."""
        ...


# ---------------------------------------------------------------------------
# Working source
# ---------------------------------------------------------------------------

class ManualSource:
    """Values typed into the form."""

    name = "Manual input"
    available = True

    def __init__(self, data: ExperimentData):
        self._data = data

    def load(self) -> ExperimentData:
        return self._data


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _Stub:
    name = "stub"
    available = False

    def load(self) -> ExperimentData:
        raise NotImplementedError(f"{self.name}: not implemented yet.")


class CsvSource(_Stub):
    """CSV file. Either summary stats per group, or per-user rows
    (then aggregate with aggregate_to_user_level first)."""

    name = "CSV file"


class ExcelSource(_Stub):
    """Excel file (.xlsx). Same formats as CsvSource."""

    name = "Excel file"


class BigQuerySource(_Stub):
    """BigQuery query that returns per-user rows or summary stats.
    Credentials come from the server's service account, never from the code."""

    name = "BigQuery"


class LookerSource(_Stub):
    """Looker Look or Explore with summary stats per group."""

    name = "Looker"


ALL_SOURCES = [ManualSource, CsvSource, ExcelSource, BigQuerySource, LookerSource]


def aggregate_to_user_level(rows, user_col: str, group_col: str, value_col: str):
    """Turn per-event rows into per-user rows (sum per user), then into
    GroupStats per group.

    Needed because tests on per-event data give too many false wins:
    events of one user are not independent.
    """
    raise NotImplementedError("aggregate_to_user_level: not implemented yet.")
