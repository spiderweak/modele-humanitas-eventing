"""
Visualization Module

This module provides the Visualizer class for generating visualizations of the simulation results.
It includes methods for plotting resource usage over time, application deployments, and final results.

Classes:
    Visualizer: Handles the visualization of simulation data.

Usage Example:
    visualizer = Visualizer()
    visualizer.visualize_environment(env)
    visualizer.apps_visualiser(env)
"""

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
        """
        Visualizes the environment including deployed applications and failed deployments.

        :param env: The simulation environment.
        :type env: Environment
        """
        # List deployed apps
        logging.info("Successfully deployed apps: ")
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
        """
        Visualizes the accepted applications over time.

        :param env: The simulation environment.
        :type env: Environment
        """
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

    def final_results(self, env: Environment):
        """
        Generates the final results of the simulation, including CPU, GPU, memory, and disk usage over time.

        :param env: The simulation environment.
        :type env: Environment
        """

        def consolidate_resource_data(env: Environment, resource_type: str):
            all_data = []
            resource_limits = {}

            for device in env.devices:
                resource_data = [list(tup) for tup in device.resource_usage_history[resource_type]] 
                resource_limits[device.id] = device.resource_limit[resource_type]

                for entry in resource_data:
                    all_data.append([device.id] + entry)

            df = pd.DataFrame(all_data, columns=['device_id', 'time', resource_type])
            df['time'] = df['time'] / (8640000 / 24)    

            """
            # Identify and print duplicate entries
            duplicates = df[df.duplicated(subset=['device_id', 'timestamp'], keep=False)]
            if not duplicates.empty:
                print("Duplicate entries found:")
                print(duplicates)
            """
            
            # Handling duplicate timestamps by averaging the values
            df = df.groupby(['device_id', 'time'], as_index=False).mean()

            df_pivot = df.pivot(index='time', columns='device_id', values=resource_type)

            # Convert resource limits to a DataFrame and align with df_pivot
            limits_series = pd.Series(resource_limits)
            df_normalized = df_pivot.div(limits_series, axis=1)

            return df_normalized

        # Create DataFrames for each resource type
        cpu_df_normalized = consolidate_resource_data(env, 'cpu')
        gpu_df_normalized = consolidate_resource_data(env, 'gpu')
        memory_df_normalized = consolidate_resource_data(env, 'mem')
        disk_df_normalized = consolidate_resource_data(env, 'disk')

        cpu_df_interpolated = cpu_df_normalized.interpolate(method='linear', axis=0, limit_direction='both')
        gpu_df_interpolated = gpu_df_normalized.interpolate(method='linear', axis=0, limit_direction='both')
        memory_df_interpolated = memory_df_normalized.interpolate(method='linear', axis=0, limit_direction='both')
        disk_df_interpolated = disk_df_normalized.interpolate(method='linear', axis=0, limit_direction='both')


        # Function to calculate statistical values for each row
        def calculate_statistics(df):
            stats_df = pd.DataFrame()
            stats_df['average'] = df.mean(axis=1)*100
            stats_df['median'] = df.median(axis=1)*100
            #stats_df['1st_quartile'] = df.apply(lambda x: np.percentile(x.dropna(), 25), axis=1)*100
            #stats_df['last_quartile'] = df.apply(lambda x: np.percentile(x.dropna(), 75), axis=1)*100

            stats_df['1st_decile'] = df.apply(lambda x: np.percentile(x.dropna(), 10), axis=1)*100
            stats_df['last_decile'] = df.apply(lambda x: np.percentile(x.dropna(), 90), axis=1)*100

            return stats_df

        # Calculate statistics for each resource type
        cpu_stats = calculate_statistics(cpu_df_interpolated)
        gpu_stats = calculate_statistics(gpu_df_interpolated)
        memory_stats = calculate_statistics(memory_df_interpolated)
        disk_stats = calculate_statistics(disk_df_interpolated)

        # Function to plot statistical values
        def plot_statistics(stats_df, title, save_as):
            plt.figure(figsize=(14, 8))

            plt.fill_between(stats_df.index, stats_df['1st_decile'], stats_df['last_decile'], color='lightgray', alpha=0.5, label='Decile Range (10-90%)')
            plt.plot(stats_df.index, stats_df['average'], color='purple', label='Average')
            plt.plot(stats_df.index, stats_df['median'], color='orange', label='Median')
            #plt.plot(stats_df.index, stats_df['last_decile'], color='black', alpha=0.25, label='Last decile (90%)')
            #plt.plot(stats_df.index, stats_df['1st_decile'], color='black', alpha=0.25, label='First decile (10%)')

            plt.axhline(y=100, color='lightgray', alpha=0.2)

            plt.xticks(ticks = range(0, 25), labels = [f'{i}' for i in range(0, 25)])

            plt.title(title)
            plt.xlabel('Time')
            plt.ylabel('Resource use (%)')
            plt.ylim(-5, 105)

            plt.legend()
            plt.savefig(save_as)

        # Plot statistics for each resource type
        plot_statistics(cpu_stats, 'CPU Resource Usage Statistics', os.path.join(env.config.output_folder,"results-cpu.png"))
        plot_statistics(gpu_stats, 'GPU Resource Usage Statistics', os.path.join(env.config.output_folder,"results-gpu.png"))
        plot_statistics(memory_stats, 'Memory Resource Usage Statistics', os.path.join(env.config.output_folder,"results-mem.png"))
        plot_statistics(disk_stats, 'Disk Resource Usage Statistics', os.path.join(env.config.output_folder,"results-disk.png"))

    def other_final_results(self, env: Environment):
        """
        Generates additional final results of the simulation, including resource usage for all devices.

        :param env: The simulation environment.
        :type env: Environment
        """
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

        plt.figure(figsize=(12, 8))  # Set the size of the plot

        # Plot each resource usage
        plt.plot(all_resources['time'], all_resources['cpu'], label='CPU Usage (%)', marker='')
        plt.plot(all_resources['time'], all_resources['gpu'], label='GPU Usage (%)', marker='')
        plt.plot(all_resources['time'], all_resources['mem'], label='Memory Usage (%)', marker='')
        plt.plot(all_resources['time'], all_resources['disk'], label='Disk Usage (%)', marker='')

        plt.title('Resource Usage Over Time')  # Title of the plot
        plt.xlabel('Time')  # X-axis label
        plt.ylabel('Usage (%)')  # Y-axis label
        plt.legend()  # Add a legend to the plot

        plt.savefig(os.path.join(env.config.output_folder, "resource_use_avg.png"))  # Display the plot

    def plot_resource_and_application_counts(self, env: Environment):
        """
        Plots resource usage and application counts over time from a CSV file.

        :param env: The simulation environment.
        :type env: Environment
        """
        # Loading data
        df = env.data.data
        df.index = df.index / (8640000 / 24)  # Convert time index to hours

        # Plotting data
        fig, ax1 = plt.subplots(figsize=(14, 8))

        # Plot CPU, GPU, Memory, and Disk averages on primary y-axis
        ax1.plot(df.index, df['cpu_avg']*100, label='CPU Avg', color='lightgray')
        ax1.plot(df.index, df['gpu_avg']*100, label='GPU Avg', color='lightgray')
        ax1.plot(df.index, df['memory_avg']*100, label='Memory Avg', color='lightgray')
        ax1.plot(df.index, df['disk_avg']*100, label='Disk Avg', color='lightgray')
        ax1.set_xlabel('Time (hours)')
        ax1.set_ylabel('Resource Usage (in %)')
        ax1.legend(loc='upper left')

        # Create a secondary y-axis to plot cumulative counts
        ax2 = ax1.twinx()
        ax2.plot(df.index, df['currently_hosted_apps'], label='Hosted Apps', color='orange', linestyle='dashed')
        ax2.plot(df.index, df['currently_hosted_procs'], label='Hosted App Components', color='orange', linestyle='dotted')
        ax2.plot(df.index, df['app_in_waiting'], label='Apps in waiting', color='yellow', linestyle='dashed')
        ax2.set_ylabel('Cumulative Counts')
        ax2.legend(loc='upper left', bbox_to_anchor=(0, 0.9))
        ax2.set_ylim([0, env.config.number_of_applications/10])
        
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))  # Offset the third y-axis
        ax3.plot(df.index, df['cumulative_app_arrival'], label='App Arrivals (cumulative)', color='magenta', linestyle='dashed')
        ax3.plot(df.index, df['cumulative_app_departure'], label='App Departures (cumulative)', color='black', linestyle='dashed')
        ax3.plot(df.index, df['cumulative_app_accepted'], label='App Accepted (cumulative)', color='green', linestyle='dashed')
        ax3.plot(df.index, df['cumulative_app_rejected'], label='App Refused (cumulative)', color='red', linestyle='dashed')
        ax3.set_ylabel('Cumulative Apps (Straight lines)')
        ax3.set_ylim([0, env.config.number_of_applications])
        ax3.legend(loc='upper right', bbox_to_anchor=(1.0, 1.0))

        ax1.set_xticks(range(0, 25, 1))
        ax1.set_xticklabels([f'{i}' for i in range(0, 25)])

        # Set plot title
        plt.title('Resource Usage and Application Counts Over Time')

        # Adjust layout
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

        file_path = os.path.join(env.config.output_folder, "global_output.png")
        plt.savefig(file_path)

        fig, ax1 = plt.subplots(figsize=(10, 6))

        # Plot CPU, GPU, Memory, and Disk averages on primary y-axis
        ax1.plot(df.index, df['cumulative_app_accepted']/df['cumulative_app_arrival']*100, label='Acceptance ratio', color='green')

        ax1.set_yticks(range(0, 101, 10))
        ax1.set_yticklabels([f'{i}' for i in range(0, 101, 10)])

        ax1.set_xticks(range(0, 25, 2))
        ax1.set_xticklabels([f'{i}' for i in range(0, 25, 2)])

        # Set plot title
        plt.title('Average Acceptance Ratio Over Time')
        file_path = os.path.join(env.config.output_folder, "acceptance.png")
        plt.savefig(file_path)

