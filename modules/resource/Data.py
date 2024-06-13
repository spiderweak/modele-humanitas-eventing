"""
This module aggregates data for output as part of the visualisation module.

The goal is to store time series with values over time for the following attributes : 

* Resources (CPU, GPU, Disk, Memory)
* Cumulative Application Arrivals/Departure
* Number of application in waiting
* Current number of application hosted
* Cumulative Number of Rejected Applications
* Cumulative Number of Accepted Applications
"""

from typing import Optional, Union
import pandas as pd
from datetime import datetime

class Data:
    def __init__(self, cpu_max=0, gpu_max=0, memory_max=0, disk_max=0, bw_max=0) -> None:
        """Initialize the DataFrame to store time series data."""
        columns = ['cpu_current', 'gpu_current', 'memory_current', 'disk_current', 'bw_current',
                   'cumulative_app_arrival', 'cumulative_app_departure', 'app_in_waiting',
                   'currently_hosted_apps', 'currently_hosted_procs', 'cumulative_app_accepted', 'cumulative_app_rejected']


        self.set_max_values(cpu_max=cpu_max, gpu_max=gpu_max, memory_max=memory_max, disk_max=disk_max, bw_max=bw_max)

        self.data = pd.DataFrame(columns=['time'] + columns).set_index('time')

        initial_data = {col: 0 for col in columns}
        initial_data['time'] = 0

        self.data.loc[0] = initial_data


    def set_max_values(self, cpu_max=0, gpu_max=0, memory_max=0, disk_max=0, bw_max=0):
        self.cpu_max = cpu_max
        self.gpu_max = gpu_max
        self.memory_max = memory_max
        self.disk_max = disk_max
        self.bw_max = bw_max


    def integrity_check(self, time):
        # Find the latest row if it exists and copy it to time-1 if necessary
        if not self.data.empty:
            latest_time = self.data.index.max()
            if latest_time < time - 1:
                self.data.loc[time - 1] = self.data.loc[latest_time].copy()

        # Ensure the row for the current time exists by copying the time-1 row
        if time - 1 not in self.data.index:
            raise ValueError(f"No data for time {time - 1} to copy from")
        if time not in self.data.index:
            self.data.loc[time] = self.data.loc[time - 1].copy()


    def update_data(self, time, key, value):
        self.data.at[time, key] += value


    def report(self):
        self.data['cpu_current'] = self.data['cpu_current'].div(self.cpu_max)
        self.data['gpu_current'] = self.data['gpu_current'].div(self.gpu_max)
        self.data['memory_current'] = self.data['memory_current'].div(self.memory_max)
        self.data['disk_current'] = self.data['disk_current'].div(self.disk_max)

        self.data.rename(columns={
            'cpu_current': 'cpu_avg',
            'gpu_current': 'gpu_avg',
            'memory_current': 'memory_avg',
            'disk_current': 'disk_avg'
        }, inplace=True)

        self.data.to_csv("output.csv")