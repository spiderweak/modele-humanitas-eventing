import logging
from modules.EventQueue import EventQueue

from typing import Optional

class Event():
    """An event that has a name, time, and priority.

    Attributes:
        name (str): The name of the event.
        queue (EventQueue): The event queue to which this event belongs.
        time (float): The time at which the event occurs.
        priority (int): The priority of the event for sorting in the queue.
    """

    REFERENCE_PRIORITY: float = 0.0

    def __init__(self, event_name: str, queue: EventQueue, event_time: Optional[int] =None):
        """Initializes an Event instance.

        Args:
            event_name (str): Name of the event.
            queue (EventQueue): The event queue to which this event belongs.
            event_time (float, optional): Time at which the event occurs. Defaults to current time.
        """
        self.queue = queue

        self.priority = self.REFERENCE_PRIORITY
        self.name = event_name
        self.time = event_time


    def __lt__(self, other :'Event') -> bool:
        """Compares this event with another based on time and priority.

        Args:
            other (Event): The other event to compare.

        Returns:
            bool: True if this event should come before the other.
        """
        return (self.time < other.time) or (self.time == other.time and self.priority < other.priority)


    def __gt__(self, other: 'Event') -> bool:
        """Compares this event with another based on time and priority.

        Args:
            other (Event): The other event to compare.

        Returns:
            bool: True if this event should come after the other.
        """
        return other < self


    def add_to_queue(self):
        """Adds this event to its associated event queue."""
        self.queue.put(self)


    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name


    @property
    def time(self) -> int:
        """Gets the time of the event."""
        return self._time

    @time.setter
    def time(self, event_time: Optional[int]) -> None:
        """Sets the time of the event.

        Args:
            event_time (int, optional): New time for the event.
        """
        self._set_time(event_time)


    def _set_time(self, event_time: Optional[int]) -> None:
        """Internal method to set the time of the event, used to avoid code duplication.

        Args:
            event_time (int, optional): New time for the event.
        """
        if event_time is None:
            self._time = self.queue.env.current_time
        elif event_time < self.queue.env.current_time:
            self._time = self.queue.env.current_time
        else:
            self._time = event_time

    @property
    def priority(self) -> float:
        """Gets the priority of the event."""
        return self._priority

    @priority.setter
    def priority(self, priority_value: float) -> None:
        """Sets the priority of the event.

        Args:
            priority_value (float): New priority value for the event.
        """
        self._priority = priority_value

    def process(self, env):
        raise ValueError("Please set an event type")