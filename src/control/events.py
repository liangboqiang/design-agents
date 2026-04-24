from __future__ import annotations

from collections import defaultdict
from typing import Callable

from schemas.event import Event

Subscriber = Callable[[Event], None]


class EventBus:
    def __init__(self, fault_reporter=None):  # noqa: ANN001
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._events: list[Event] = []
        self._fault_reporter = fault_reporter

    def set_fault_reporter(self, fault_reporter) -> None:  # noqa: ANN001
        self._fault_reporter = fault_reporter

    def subscribe(self, event_name: str, callback: Subscriber) -> None:
        self._subscribers[event_name].append(callback)

    def emit(self, event_name: str, **payload) -> Event:
        event = Event(name=event_name, payload=payload)
        self._events.append(event)
        for callback in self._subscribers.get(event_name, []):
            self._deliver(event_name, callback, event)
        for callback in self._subscribers.get("*", []):
            self._deliver(event_name, callback, event)
        return event

    def recent(self, limit: int = 20) -> list[Event]:
        return self._events[-limit:]

    def _deliver(self, event_name: str, callback: Subscriber, event: Event) -> None:
        try:
            callback(event)
        except Exception as exc:  # noqa: BLE001
            if self._fault_reporter is None:
                return
            self._fault_reporter(
                phase="event_emit",
                source_type="event_subscriber",
                source_name=self._callback_name(callback),
                exc=exc,
                context={"event_name": event_name},
                emit_event=False,
            )

    @staticmethod
    def _callback_name(callback: Subscriber) -> str:
        return str(getattr(callback, "__qualname__", None) or getattr(callback, "__name__", None) or repr(callback))
