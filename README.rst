Welcome to the Humanitas Network and Services Simulator's documentation
=======================================================================

This program is designed as a simulation tool to experiment with application placement under operational constraints for HEAVEN.

Overview
--------

The Humanitas Network and Services Simulator is built with modularity in mind, allowing replaceable building blocks that can interoperate with other Humanitas tools. Key modules include device generation, application generation, application arrivals generation, simulation processing, and archival of results.

Running the Program
-------------------

The program can be executed either as a whole or step-by-step. It is typically run using an automation tool like Airflow.

Global Simulation
+++++++++++++++++

To run the overall simulation, use the following command:

      python __main__.py

This command uses the default `config.yaml` file and example files, which provide default values for various parameters. The simulation generates a graph saved as *fig/graph.png* and plots deployment results in *fig/results.png*.

Step-by-Step Execution
++++++++++++++++++++++

For more granular control, you can execute each component individually. This approach facilitates exports and allows concurrent runs of different placement algorithms for testing and comparison.

Execute the following commands in sequence:

      python DeviceGenerator.py
      python AppGenerator.py
      python PlacementGenerator.py
      python Processing.py
      python Archiver.py

Modules
-------

DeviceGenerator
+++++++++++++++

The **DeviceGenerator** uses the `config.yaml` device files, specifically from *template_files/devices* and *device_number*, to generate a device graph. The generated device information is stored in a JSON file (defaults to *latest/devices.json*) with device characteristics and a routing table.

AppGenerator
++++++++++++

The **AppGenerator** uses the `config.yaml` application files, primarily from *template_files/application* and *application_number*, to generate application characteristics. Applications are defined as a list of processes (Processus) that request resources from allocated devices. The generated applications are stored in *latest/applications.json*, with a default of generating 5000 applications.

PlacementGenerator
++++++++++++++++++

The **PlacementGenerator** creates a queue of *Placement* events that simulate application arrivals. Each event includes the event time, application ID, and device requester ID, and is exported to a JSON file for the Processing algorithm.

Processing
++++++++++

The **Processing** module is the core of the simulator. It loads information from previous modules, processes the simulation queue, and exports the data to a results.csv file. The processing currently uses bi-partite graphs but will be enhanced for other placement algorithms.

Visualizer
++++++++++

The **Visualizer** imports pre-processed data and generates graphs for articles. It extracts data from the *latest* folder and saves it to a dated folder, with the default date set to today. For Airflow, the date string is formatted as:

      date_string = datetime.datetime.now().isoformat(timespec='minutes').replace(":", "-")[:-1]+"0"
      python Visualizer.py --date=data/{date_string}


Features
--------

- Modular design for easy replacement and integration with other tools.
- Comprehensive simulation with configurable parameters.
- Detailed logging and archival of results.

TODO
----

- Enhance the processing unit for additional placement algorithms.

Configuration
-------------

Refer to `config.yaml` for parameter settings and customization options.

Contact
-------

For questions or contributions, please contact the development team at [your_contact_info].
