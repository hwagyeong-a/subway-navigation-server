"""Team A ↔ Team B integration boundary.

Team B replaces the default stub by calling register_estimator() at app
startup. See CLAUDE.md "Team B integration boundary".
"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class WifiSample:
    bssid: str
    rssi: float  # int·float 모두 허용 (앱이 최근 N개 평균을 보내면 float)


LocationEstimator = Callable[[list[WifiSample]], str]


def _stub_estimator(samples: list[WifiSample]) -> str:
    raise NotImplementedError(
        "No estimator registered. "
        "Team B: call register_estimator(your_knn_fn) at app startup."
    )


_estimator: LocationEstimator = _stub_estimator


def register_estimator(fn: LocationEstimator) -> None:
    global _estimator
    _estimator = fn


def estimate(samples: list[WifiSample]) -> str:
    return _estimator(samples)
