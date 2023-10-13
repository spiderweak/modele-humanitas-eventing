from modules.EventQueue import EventQueue
from modules.events.Event import Event

class Movement(Event):
    def __init__(self, event_name, queue: EventQueue, event_time=None):
        super().__init__(event_name, queue, event_time)
        raise NotImplementedError('Process not implemented')