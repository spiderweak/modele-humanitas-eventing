from modules.events.Event import Event

class FinalReport(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        self.priority = 0

    def process(self, env):
        for device in env.devices:
            device.report_on_value(self.time)

        env.data.report(folder = env.config.output_folder)
