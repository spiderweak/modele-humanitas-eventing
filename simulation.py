import matplotlib.pyplot as plt
import networkx as nx
import random

from modules.Application import Application
from modules.PhysicalNetworkLink import PhysicalNetworkLink
from modules.CustomExceptions import NoRouteToHost

# GLOBAL VARIABLES (bad practice)
N_DEVICES = 40
wifi_range = 9


def custom_distance(x1, y1, z1, x2, y2, z2):
    """
    Defines a custom distance for device wireless coverage to account for less coverage due to floor interception.

    Args:
        x1 : x value, device 1
        z1 : z value, device 1
        y1 : y value, device 1
        x2 : x value, device 2
        y2 : y value, device 2
        z2 : z value, device 2

    Returns:
        distance : int, distance (as coverage) between device 1 and device 2.
    """
    distance = ((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)**0.5
    return distance


def generate_and_plot_devices_positions(devices):
    """
    Defines random devices position
    Each device will be represented with its coordinates (x, y, z)

    Args:
        devices : list, List of coords

    Returns:
        None
    """
    n_devices = N_DEVICES # Number of devices

    floor_size_x = 40 # in meters
    floor_size_y = 40 # in meters


    for j in range(n_devices):
        # Processing device position, random x, y, z fixed to between various values (z=0 for now)
        x = round(random.random() * floor_size_x,2)
        y = round(random.random() * floor_size_y,2)
        z = 0

        devices.append([x,y,z])


    # We'll try our hand on plotting everything in a graph

    # Creating a graph
    G = nx.Graph()

    # We add the nodes, our devices, to our graph
    for i in range(len(devices)):
        G.add_node(i, pos=devices[i])

    # We add the edges, to our graph, which correspond to wifi reachability

    for i in range(len(devices)):
        for j in range(i+1, len(devices)):
            distance = custom_distance(devices[i][0],devices[i][1],devices[i][2],devices[j][0],devices[j][1],devices[j][2])
            if distance < wifi_range:
                ### We add edges if we have coverage
                G.add_edge(i, j)

    # Let's try plotting the network

    # We alread have the coords, but let's process it again just to be sure
    x_coords, y_coords, z_coords = zip(*devices)

    #  We create a 3D scatter plot again
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot()

    # Lets trace the graph by hand
    ## Placing the nodes
    ax.scatter(x_coords, y_coords, c='b')
    ## Placing the edges by hand
    for i, j in G.edges():
        ax.plot([devices[i][0], devices[j][0]],
                [devices[i][1], devices[j][1]], c='lightgray')

    # Set the labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    # Title
    ax.set_title(f'Undirected Graph of Devices with Edge Distance < {wifi_range}')

    # Saves the graph in a file
    plt.savefig("fig/graph.png")


    # Let's try to code a routing table
def generate_routing_table(devices_list, physical_network_link_list):
    """
    Generates a routing table on each device
    The function first lists the neighboring device, then iterate on the list to build a routing table based on shortest distance among links

    Args:
        devices : list, List of coords
        physical_network_link_list: list, Lists the physical links between devices

    Returns:
        None
    """
    for device_1 in devices_list:
        device_1_id = device_1.getDeviceID()
        for device_2 in devices_list:
            device_2_id = device_2.getDeviceID()
            distance = custom_distance(device_1.x,device_1.y,device_1.z,device_2.x,device_2.y,device_2.z)
            new_physical_network_link_id = device_1_id*len(devices_list) + device_2_id
            if distance < wifi_range:
                device_1.addToRoutingTable(device_2_id, device_2_id, distance)
                device_2.addToRoutingTable(device_1_id, device_1_id, distance)
                new_physical_network_link = PhysicalNetworkLink(device_1_id, device_2_id)
                new_physical_network_link.setLinkID(new_physical_network_link_id)
                if device_1_id == device_2_id:
                    new_physical_network_link.setPhysicalNetworkLinkLatency(0)
                physical_network_link_list[new_physical_network_link_id] = new_physical_network_link
            else:
                new_physical_network_link = PhysicalNetworkLink()
                physical_network_link_list[new_physical_network_link_id] = None

    ## We iterate on the matrix:

    changes = True

    while(changes):
        ## As long as the values change
        changes = False
        for i in range(len(devices_list)):
            for j in range(len(devices_list)):
                device_1_id = devices_list[i].getDeviceID()
                device_2_id = devices_list[j].getDeviceID()

                try:
                    next_hop,distance = devices_list[i].getRouteInfo(device_2_id)
                except NoRouteToHost:
                    next_hop,distance = (-1,1000)

                nh_array = [next_hop]
                dist_array = [distance]
                for k in range(len(devices_list)):
                    device_3_id = devices_list[k].getDeviceID()
                    try:
                        next_hop_1_3,distance_1_3 = devices_list[i].getRouteInfo(device_3_id)
                    except NoRouteToHost:
                        next_hop_1_3,distance_1_3 = (-1,1000)

                    try:
                        _,distance_3_2 = devices_list[k].getRouteInfo(device_2_id)
                    except NoRouteToHost:
                        distance_3_2 = 1000

                    nh_array.append(next_hop_1_3)
                    dist_array.append(distance_1_3 + distance_3_2)

                min_index = dist_array.index(min(dist_array))
                min_nh = nh_array[min_index]
                min_array = dist_array[min_index]

                if min_array < distance:
                ## If we observe any change, update and break the loop
                    changes = True
                    devices_list[i].addToRoutingTable(device_2_id, min_nh, min_array)


# Now, we can play with deployments
def simulate_deployments(devices_list, physical_network_link_list):
    """
    Simulates a complete deployment.
    Simulates 200 successive application deployments.

    Args:
        devices : list, List of coords
        physical_network_link_list: list, Lists the physical links between devices

    Returns:
        None
    """
    testings = 200

    latency_array = [0]
    operational_latency_array = [0]
    app_refused_array = [0]
    app_success_array = [0]
    proc_success_array = [0]
    trivial_array = [0]

    for i in range(testings):
        trivial = 0
        application = Application()
        application.randomAppInit()
        application.setAppID(i)

        # select a random device
        device_id = random.choice(range(len(devices_list)))

        # deploy on device, get associated deployed status and latency
        success, latency, operational_latency, deployed_onto_devices = application_deploy(application, devices_list[device_id], devices_list, physical_network_link_list)

        latency_array.append(latency_array[-1]+latency)
        operational_latency_array.append(operational_latency_array[-1]+operational_latency)

        if application.num_procs !=1 and len(set(deployed_onto_devices)) == 1:
            trivial = 1

        trivial_array.append(trivial_array[-1]+trivial)

        if success:
            app_success_array.append(app_success_array[-1]+1)
            app_refused_array.append(app_refused_array[-1])
            proc_success_array.append(proc_success_array[-1]+len(deployed_onto_devices))

        else:
            app_success_array.append(app_success_array[-1])
            app_refused_array.append(app_refused_array[-1]+1)
            proc_success_array.append(proc_success_array[-1])



    fig = plt.figure(figsize=(10, 10))
    ax1 = fig.add_subplot()

    ax1.set_ylabel('latency')
    ax1.plot(latency_array, label = 'Deployment Latency', color = 'b')
    ax1.plot(operational_latency_array, label = 'Operational latency', color = 'c')
    ax1.legend()

    ax2 = ax1.twinx()
    ax2.set_ylabel('# of apps (deployed or refused)')
    ax2.set_ylim(0,300)
    ax2.plot(proc_success_array, label = 'Successful processus deployments', color = 'g')
    ax2.plot(app_success_array, label = 'Successful application deploy', color = 'orange')
    ax2.plot(app_refused_array, label = 'Failed application deploy', color = 'r')
    ax2.plot(trivial_array, label = 'Trivial application deploy', color = 'black')
    ax2.legend()

    # Set the labels
    # Title
    ax1.set_title(f'Deployment results')

    # Print the graph
    plt.savefig("fig/results.png")