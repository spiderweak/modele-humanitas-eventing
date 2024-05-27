import logging
import os

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from modules.Environment import Environment

class Visualizer():

    def __init__(self):
        pass


    def visualize_environment(self, env: Environment):

        # List deployed apps
        logging.info("Successfully deployed apps : ")
        logging.info(env.list_accepted_application)

        logging.info("Application deployment failures: ")
        logging.info(env.rejected_application_by_reason)

        logging.info(f"Number of rejection : {sum([len(reason) for reason in env.rejected_application_by_reason.values()])} ")

        data = env.get_device_by_id(12).resource_usage_history['cpu']

        x,y = zip(*data)

        plt.clf()
        plt.plot(x,y)
        plt.title("CPU consumption over time")
        plt.xlabel("Time (in s)")
        plt.ylabel("Theoretical CPU usage")

        logging.debug(data)
        plt.savefig(os.path.join(env.config.output_folder, "results.png"))


    def apps_visualiser(self, env: Environment):
        times, values = zip(*env.count_accepted_application)

        plt.clf()
        # Set the labels
        plt.plot(times, values)
        plt.title("Accepted Applications Over Time")
        plt.xlabel("Time (in s)")
        plt.ylabel("Number of Accepted Applications")

        plt.savefig(os.path.join(env.config.output_folder, "accepted.png"))


        logging.info(f"Number of accepted applications : {values[-1]}")

        times, values = zip(*env.count_tentatives)

        plt.clf()
        # Set the labels
        plt.plot(times, values)
        plt.title("Counting Tentatives with success Time")
        plt.xlabel("Time (in s)")
        plt.ylabel("Number of Tentatives with success")

        plt.savefig(os.path.join(env.config.output_folder, "tentatives_with_success.png"))


    def final_results(self, env):

        cpu_data = dict()
        cpu_limit_data = dict()

        gpu_data = dict()
        gpu_limit_data = dict()

        mem_data = dict()
        mem_limit_data = dict()

        disk_data = dict()
        disk_limit_data = dict()

        max_time = 0
        time = 0

        for device in env.devices:

            previous_time, previous_value = (0,0)

            cpu_data[device.id] = [(previous_time, previous_value)]
            cpu_limit_data[device.id] = device.resource_limit['cpu']

            for time,value in device.resource_usage_history['cpu']:
                if time != previous_time:
                    cpu_data[device.id].append((time,value-previous_value))
                    previous_time = time
                    previous_value = value

            max_time = max(time, max_time)

            previous_time, previous_value = (0,0)
            gpu_data[device.id] = [(previous_time, previous_value)]
            gpu_limit_data[device.id] = device.resource_limit['gpu']

            for time,value in device.resource_usage_history['gpu']:
                if time != previous_time:
                    gpu_data[device.id].append((time,value-previous_value))
                    previous_time = time
                    previous_value = value

            max_time = max(time, max_time)

            previous_time, previous_value = (0,0)
            mem_data[device.id] = [(previous_time, previous_value)]
            mem_limit_data[device.id] = device.resource_limit['mem']

            for time,value in device.resource_usage_history['mem']:
                if time != previous_time:
                    mem_data[device.id].append((time,value-previous_value))
                    previous_time = time
                    previous_value = value

            max_time = max(time, max_time)

            previous_time, previous_value = (0,0)
            disk_data[device.id] = [(previous_time, previous_value)]
            disk_limit_data[device.id] = device.resource_limit['disk']

            for time,value in device.resource_usage_history['disk']:
                if time != previous_time:
                    disk_data[device.id].append((time,value-previous_value))
                    previous_time = time
                    previous_value = value


            max_time = max(time, max_time)

        cpu_data_unpacked = dict()
        for _,v1 in cpu_data.items():
            for k2,v2 in v1:
                try:
                    cpu_data_unpacked[k2] += v2
                except KeyError:
                    cpu_data_unpacked[k2] = v2

        gpu_data_unpacked = dict()
        for _,v1 in gpu_data.items():
            for k2,v2 in v1:
                try:
                    gpu_data_unpacked[k2] += v2
                except KeyError:
                    gpu_data_unpacked[k2] = v2

        mem_data_unpacked = dict()
        for _,v1 in mem_data.items():
            for k2,v2 in v1:
                try:
                    mem_data_unpacked[k2] += v2
                except KeyError:
                    mem_data_unpacked[k2] = v2

        disk_data_unpacked = dict()
        for _,v1 in disk_data.items():
            for k2,v2 in v1:
                try:
                    disk_data_unpacked[k2] += v2
                except KeyError:
                    disk_data_unpacked[k2] = v2

        df = pd.DataFrame(index=range(max_time), columns=['cpu', 'gpu', 'mem', 'disk'])

        df['cpu'] = 0
        df['gpu'] = 0
        df['mem'] = 0
        df['disk'] = 0

        print("\n\nDumping Output in results file")

        for t in tqdm(range(1,max_time)):
            try:
                df.loc[t,'cpu'] = df.loc[t-1,'cpu'] + cpu_data_unpacked[t]
            except KeyError:
                df.loc[t,'cpu'] = df.loc[t-1,'cpu']
            try:
                df.loc[t,'gpu'] = df.loc[t-1,'gpu'] + gpu_data_unpacked[t]
            except KeyError:
                df.loc[t,'gpu'] = df.loc[t-1,'gpu']
            try:
                df.loc[t,'mem'] = df.loc[t-1,'mem'] + mem_data_unpacked[t]
            except KeyError:
                df.loc[t,'mem'] = df.loc[t-1,'mem']
            try:
                df.loc[t,'disk'] = df.loc[t-1,'disk'] + disk_data_unpacked[t]
            except KeyError:
                df.loc[t,'disk'] = df.loc[t-1,'disk']

        # Percentages

        df['cpu'] = df['cpu'] / sum(v for _,v in cpu_limit_data.items()) * 100
        df['gpu'] = df['gpu'] / sum(v for _,v in gpu_limit_data.items()) * 100
        df['mem'] = df['mem'] / sum(v for _,v in mem_limit_data.items()) * 100
        df['disk'] = df['disk'] / sum(v for _,v in disk_limit_data.items())* 100

        df.to_csv(os.path.join(env.config.output_folder, "results.csv"))

        # Can be good to keep track on deployment requests, failures, and eventually to backoff placement failures

    def other_final_results(self, env):
        # Initialize a DataFrame to store aggregated data
        resource_types = ['cpu', 'gpu', 'mem', 'disk']
        all_resources = pd.DataFrame()

        # Iterate over each device
        for device in tqdm(env.devices):
            for resource in resource_types:
                # Load resource usage into a DataFrame
                data = pd.DataFrame(device.resource_usage_history[resource], columns=['time', resource])
                data.set_index('time', inplace=True)

                # Assume unchanged resource usage until the next change (forward fill)
                data = data.reindex(range(data.index.min(), data.index.max() + 1), method='ffill')

                # If this is the first device, initialize the DataFrame; otherwise, add the data
                if all_resources.empty:
                    all_resources = data
                else:
                    # Aggregate by adding new data to the existing sum for each resource
                    all_resources = all_resources.add(data, fill_value=0)

        # Normalize by total capacity of each resource across all devices
        total_limits = {resource: sum(device.resource_limit[resource] for device in env.devices) for resource in resource_types}
        for resource in resource_types:
            all_resources[resource] /= total_limits[resource]
            all_resources[resource] *= 100  # Convert to percentage

        all_resources = all_resources.round(1)
        
        all_resources.to_csv(os.path.join(env.config.output_folder, "results.csv"))
        all_resources = pd.read_csv(os.path.join(env.config.output_folder, "results.csv"))

        plt.figure(figsize=(12, 8))  # Set the size of the plot
        
        # Plot each resource usage
        plt.plot(all_resources['time'], all_resources['cpu'], label='CPU Usage (%)', marker='')
        plt.plot(all_resources['time'], all_resources['disk'], label='Disk Usage (%)', marker='')
        plt.plot(all_resources['time'], all_resources['gpu'], label='GPU Usage (%)', marker='')
        plt.plot(all_resources['time'], all_resources['mem'], label='Memory Usage (%)', marker='')
        
        plt.title('Resource Usage Over Time')  # Title of the plot
        plt.xlabel('Time')  # X-axis label
        plt.ylabel('Usage (%)')  # Y-axis label
        plt.legend()  # Add a legend to the plot
        plt.grid(True)  # Add gridlines for better readability
        
        plt.savefig(os.path.join(env.config.output_folder, "resource_use_avg.png"))  # Display the plot

