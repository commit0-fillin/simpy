"""
Core components for event-discrete simulation environments.

"""
from __future__ import annotations
from heapq import heappop, heappush
from itertools import count
from types import MethodType
from typing import TYPE_CHECKING, Any, Generic, Iterable, List, Optional, Tuple, Type, TypeVar, Union
from simpy.events import NORMAL, URGENT, AllOf, AnyOf, Event, EventPriority, Process, ProcessGenerator, Timeout
Infinity: float = float('inf')
T = TypeVar('T')

class BoundClass(Generic[T]):
    """Allows classes to behave like methods.

    The ``__get__()`` descriptor is basically identical to
    ``function.__get__()`` and binds the first argument of the ``cls`` to the
    descriptor instance.

    """

    def __init__(self, cls: Type[T]):
        self.cls = cls

    def __get__(self, instance: Optional[BoundClass], owner: Optional[Type[BoundClass]]=None) -> Union[Type[T], MethodType]:
        if instance is None:
            return self.cls
        return MethodType(self.cls, instance)

    @staticmethod
    def bind_early(instance: object) -> None:
        """Bind all :class:`BoundClass` attributes of the *instance's* class
        to the instance itself to increase performance."""
        for name, attr in instance.__class__.__dict__.items():
            if isinstance(attr, BoundClass):
                setattr(instance, name, attr.__get__(instance, instance.__class__))

class EmptySchedule(Exception):
    """Thrown by an :class:`Environment` if there are no further events to be
    processed."""

class StopSimulation(Exception):
    """Indicates that the simulation should stop now."""

    @classmethod
    def callback(cls, event: Event) -> None:
        """Used as callback in :meth:`Environment.run()` to stop the simulation
        when the *until* event occurred."""
        raise StopSimulation()
SimTime = Union[int, float]

class Environment:
    """Execution environment for an event-based simulation. The passing of time
    is simulated by stepping from event to event.

    You can provide an *initial_time* for the environment. By default, it
    starts at ``0``.

    This class also provides aliases for common event types, for example
    :attr:`process`, :attr:`timeout` and :attr:`event`.

    """

    def __init__(self, initial_time: SimTime=0):
        self._now = initial_time
        self._queue: List[Tuple[SimTime, EventPriority, int, Event]] = []
        self._eid = count()
        self._active_proc: Optional[Process] = None
        BoundClass.bind_early(self)

    @property
    def now(self) -> SimTime:
        """The current simulation time."""
        return self._now

    @property
    def active_process(self) -> Optional[Process]:
        """The currently active process of the environment."""
        return self._active_proc
    if TYPE_CHECKING:

        def process(self, generator: ProcessGenerator) -> Process:
            """Create a new :class:`~simpy.events.Process` instance for
            *generator*."""
            pass

        def timeout(self, delay: SimTime=0, value: Optional[Any]=None) -> Timeout:
            """Return a new :class:`~simpy.events.Timeout` event with a *delay*
            and, optionally, a *value*."""
            pass

        def event(self) -> Event:
            """Return a new :class:`~simpy.events.Event` instance.

            Yielding this event suspends a process until another process
            triggers the event.
            """
            pass

        def all_of(self, events: Iterable[Event]) -> AllOf:
            """Return a :class:`~simpy.events.AllOf` condition for *events*."""
            pass

        def any_of(self, events: Iterable[Event]) -> AnyOf:
            """Return a :class:`~simpy.events.AnyOf` condition for *events*."""
            pass
    else:
        process = BoundClass(Process)
        timeout = BoundClass(Timeout)
        event = BoundClass(Event)
        all_of = BoundClass(AllOf)
        any_of = BoundClass(AnyOf)

    def schedule(self, event: Event, priority: EventPriority=NORMAL, delay: SimTime=0) -> None:
        """Schedule an *event* with a given *priority* and a *delay*."""
        heappush(self._queue, (self._now + delay, priority, next(self._eid), event))

    def peek(self) -> SimTime:
        """Get the time of the next scheduled event. Return
        :data:`~simpy.core.Infinity` if there is no further event."""
        return self._queue[0][0] if self._queue else Infinity

    def step(self) -> None:
        """Process the next event.

        Raise an :exc:`EmptySchedule` if no further events are available.

        """
        try:
            self._now, _, _, event = heappop(self._queue)
        except IndexError:
            raise EmptySchedule()

        # Process the event
        event._ok = True
        event._value = event._callback(event)
        event._defused = False

        if not event._defused:
            event._defused = True

        if isinstance(event, Process):
            self._active_proc = event
        else:
            self._active_proc = None

    def run(self, until: Optional[Union[SimTime, Event]]=None) -> Optional[Any]:
        """Executes :meth:`step()` until the given criterion *until* is met.

        - If it is ``None`` (which is the default), this method will return
          when there are no further events to be processed.

        - If it is an :class:`~simpy.events.Event`, the method will continue
          stepping until this event has been triggered and will return its
          value.  Raises a :exc:`RuntimeError` if there are no further events
          to be processed and the *until* event was not triggered.

        - If it is a number, the method will continue stepping
          until the environment's time reaches *until*.

        """
        if until is not None:
            if not isinstance(until, Event):
                # Assume until is a number
                at = float(until)
                if at <= self.now:
                    raise ValueError(f'until={at} must be > the current simulation time')
                until = self.timeout(at - self.now)

            until.callbacks.append(StopSimulation.callback)

        try:
            while True:
                self.step()
        except StopSimulation as stop:
            return until.value if isinstance(until, Event) else None
        except EmptySchedule:
            if until is not None and not until.triggered:
                raise RuntimeError(f'No scheduled events left but "until" event was not triggered: {until}')
