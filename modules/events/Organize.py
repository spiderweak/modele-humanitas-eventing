import logging

from modules.Environment import Environment

from modules.events.Event import Event
from modules.fullstateprocessing.FullStateProcessing import CeilingUnlimitedMigration


class Organize(Event):
    def __init__(self, event_name, queue, application_to_place, event_time=None):
        super().__init__(event_name, queue, event_time)
        self.priority = 5
        self.application_to_place = application_to_place

    def process(self, env: Environment):

        dev_matrix = env.extract_devices_resources()
        dev_weight = env.extract_decision_weights()
        proc_matrix = env.extract_apps_data_in_batch()
        instance = CeilingUnlimitedMigration(proc_matrix, dev_matrix, dev_weight)

        x = instance.processing()

        return x
