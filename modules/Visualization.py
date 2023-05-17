import logging

from modules.Device import Device
from modules.Environment import Environment

import matplotlib.pyplot as plt

class Visualizer():

    def __init__(self):
        pass

    def visualize_environment(self, env):

        data = env.getDeviceByID(3).cpu_usage_history

        x,y = zip(*data)

        plt.plot(x,y)

        logging.info(data)
        plt.savefig("fig/results.png")
