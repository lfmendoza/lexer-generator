"""Compile pipeline trace events."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TraceEventKind(str, Enum):
    SPEC_PARSED = "SPEC_PARSED"
    TREES_EMITTED = "TREES_EMITTED"
    NFA_BUILT = "NFA_BUILT"
    DFA_BUILT = "DFA_BUILT"
    DFA_MINIMIZED = "DFA_MINIMIZED"
    CODE_WRITTEN = "CODE_WRITTEN"
    DFA_DOT_WRITTEN = "DFA_DOT_WRITTEN"


@dataclass
class TraceEvent:
    kind: TraceEventKind
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class TraceRecorder:
    def __init__(
        self,
        mode: str = "human",
        sink: Callable[[str], None] | None = None,
    ) -> None:
        self.mode = mode
        self._sink = sink or (lambda s: print(s, flush=True))

    def enabled(self) -> bool:
        return self.mode != "off"

    def emit(self, kind: TraceEventKind, **data: Any) -> None:
        if not self.enabled():
            return
        ev = TraceEvent(kind=kind, data=dict(data))
        if self.mode == "json":
            self._sink(
                json.dumps(
                    {"kind": ev.kind.value, "ts": ev.timestamp, "data": ev.data},
                    ensure_ascii=False,
                )
            )
        else:
            parts = [f"[trace] {ev.kind.value}"]
            for k, v in ev.data.items():
                parts.append(f"{k}={v}")
            self._sink(" ".join(parts))


def null_trace() -> TraceRecorder:
    return TraceRecorder(mode="off")
