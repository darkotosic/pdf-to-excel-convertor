from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class ProgressUpdate:
    completed: int
    total: int
    message: str


ProgressCallback = Callable[[ProgressUpdate], None]
