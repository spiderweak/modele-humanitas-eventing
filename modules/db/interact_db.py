import sqlite3
import random
from modules.Device import Device


def create_db(device_db):
    """
    Creates an empty device table to store device features (CPU, GPU, Mem, Disk...)
    The module uses SQLite for now but will be migrated to network connected database further in the project (MariaDB, MySQL, ProstgreSQL)

    Args:
        None
        Will be updated to add the database address

    Returns:
        None
    """
    con = sqlite3.connect(device_db)
    cur = con.cursor()
    cur.execute("CREATE TABLE device(id, x, y, z, cpu_limit, gpu_limit, mem_limit, disk_limit, cpu_usage, gpu_usage, mem_usage, disk_usage)")
    # Need to find a way to store the routing table

def populate_db(devices, device_db):
    """
    Populates the database with randomly generated devices.
    Positions are provided in input.
    Untested with existing table, will probably need to create an update function.

    Args:
        devices: list([int,int]), devices coordinates in a 2d space, will need to be updated for 3D support

    Returns:
        None
    """
    con = sqlite3.connect(device_db)
    cur = con.cursor()
    data = list()
    for i in range(len(devices)):
        new_device_cpu = random.choice([2,4,8])
        new_device_gpu = random.choice([4,8,12,16])
        new_device_mem = random.choice([4,8,16,24,32]) * 1024
        new_device_disk = random.choice([50, 100, 125, 250, 500]) * 1024
        #device(id, x, y, z, cpu_limit, gpu_limit, mem_limit, disk_limit, cpu_usage, gpu_usage, mem_usage, disk_usage)
        data.append((i, devices[i][0],devices[i][1],0, new_device_cpu, new_device_gpu, new_device_mem, new_device_disk, 0, 0, 0, 0))

    cur.executemany("INSERT INTO device VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)

    con.commit()
    con.close()

def dump_from_db(devices_list, device_db):
    """
    Dumps the database's content in the devices_list list to work with the remaining parts of the script.
    Function will need to be updated to fit needs when handling inputs/outputs.

    Args:
        devices_list: list(Device), list of devices objects, devices will be replaced if already in the list, unreferenced devices will be set as None in the list.

    Returns:
        None
    """
    con = sqlite3.connect(device_db)
    cur = con.cursor()
    for row in cur.execute("SELECT * FROM device"):
        device = Device()

        if device.getDeviceID() != row[0]:
            device.setDeviceID(row[0])

        device.setDevicePosition(row[1], row[2], row[3])

        device.setDeviceCPULimit(row[4])
        device.setDeviceGPULimit(row[5])
        device.setDeviceMemLimit(row[6])
        device.setDeviceDiskLimit(row[7])

        device.setDeviceCPUUsage(0,row[8])
        device.setDeviceGPUUsage(0,row[9])
        device.setDeviceMemUsage(0,row[10])
        device.setDeviceDiskUsage(0,row[11])

        if len(devices_list) <= device.getDeviceID():
            for i in range(device.getDeviceID()-len(devices_list)+1):
                devices_list.append(None)

        devices_list[device.getDeviceID()] = device
