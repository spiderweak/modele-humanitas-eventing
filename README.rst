Welcome to the Embedded Application Choreography Simulation's documentation
===========================================================================

This program was designed as a simulation tool to experiment around application placement under operational constraint for HEAVEN.

Running the program
-------------------

The program is designed around a few modules that perform device generation, application generation, application arrivals generation, simulation processing and simulation results exports and archival.

The reason behind this design is to develop a simulation system with replaceable building blocks, that could be interoperable with other Humanitas tools.

The program is usually run by an automation tool called Airflow. Airflow sets up the input by running all generators modules, then runs the processing module once input data is generated. Finally, the archiver exports simulation input/output to an archives folder for further studies and research articles 

Global simulation
+++++++++++++++++

Running the overall simulation is possible with the following commands::

   python __main__.py

If the program is downloaded from the repo, it comes with a default config.yaml file and example files that gives default values for various parameters, allowing a complete simulation run.

The global simulation creates a graph saved under *fig/graph.png* and plots successful and rejected application deployment, as well as latency, on a given plot under the *fig/results.png* file

Step by step execution
++++++++++++++++++++++

When running the program with Airflow, or in "step-by-step" mode, the overall program is splitted in all its components to facilitate exports and concurrent runs of different placement algorithms for tests and comparisons.

The step-by-step execution consists in running the following commands successively::

   python DeviceGenerator.py
   python AppGenerator.py
   python PlacementGenerator.py
   python Processing.py
   python Archiver.py

DeviceGenerator
---------------

The **DeviceGenerator** program takes into account the information from the config.yaml device files, mostly from *template_files/devices* and *device_number* to generate a graph of devices.

The files provided as examples under the examples folder are data for a given example device placement from Humanitas, as well as a personal test with a good device random generation.

Based on the device positions from either files or another random device placement file, a JSON file is written (defaults under *latest/devices.json*) with all devices characteristics as well as a single hop routing table for to determine optimal path when running the simulation.


AppGenerator
------------

The **AppGenerator** program takes into account the information from the config.yaml applications files, mostly from *template_files/application* and *application_number* to generate applications characteristics.

An Application` is defined as a List of Processus that will request resources from their allocated devices. Randomly generated application are made of a random number of distributable processus as well as link usage requests between them.

The **AppGenerator** store an export for all generated application under *latest/applications.json*. Defaults to generating 5000 applications.

PlacementGenerator
------------------

The simulator revolves around processing a queue of Application Placement Requests, that simulate application arrivals based on the studied scenario, such as resource requests from other programs, from on-site hardware or from users.

The **PlacementGenerator** program generates a queue of *Placement* events, each event has a event_time, application id and device requester id associated.

These informations are then exported to a JSON file, in order to be loaded by the Processing algorithm.
