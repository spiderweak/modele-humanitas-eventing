# modèle-humanitas-instant

## Getting started

This program was first designed as a simulation tool to experiment around application placement under operational constraint for HEAVEN.

It was not built under the assumption that it would run in production before a long time, it was adapted to provide a single placement for application under time constraints.

### Running the program

To test a single application deployment, the fastest way is to run the modelisation-2d python script :

```
python modelisation-2d.py
```

This program opens the device information from the db.sqlite file (creates a random disposition if the database is empty), creates a mapping based on distance between virtual device, creates a routing table based on shortest path along the graph, then test the application deployment.

The application_deploy function returns the mapping between virtual (docker) process and device (based on device ID)

### Global simulation

Running the overall simulation is possible with the --simulation=True flag

```
python modelisation-2d.py --simulate=True
```

The global simulation creates a graph saved under *fig/graph.png* and plots successful and rejected application deployment, as well as latency, on a given plot under the *fig/results.png* file

Other possible argument are listed when running 

```
python modelisation-2d.py -h
```

## Finding what you need

### Configuration

The project provides two, short, test-configuration files.

The config.yaml configuration provides the database location as well as loglevel and logfile.

The app.yaml file is an application example in the way it must be fed to the Application and Processus modules. This serves as an example to the kind of information needed to indicate the constraints necessary to deploy a given application.

Note that application resource request values are high in order to test multiple-devices deployment.

### Modules

The project is built around a few classes (Application, Device, Processus, Path...) that are described under the modules folder. The classes described under these modules handle the various resources that are used as part of the program (CPU/GPU/Memory/DiskSpace):
- The Device module includes the methods to read (virtual) device state once extracted from the database and store current and maximal resource values.
- The PhysicalNetworkLink module provides a short implementation regarding virtualized physical links between devices, it is used for bandwidth allocation and routing is done along such links.
- The Application module describes application as a list of processus and links between those processus.
- The Processus module lists the resource request associated with application processus.
- The Path module generates path between physical devices to handle 

Additionally, a db folder, in the modules folder, hosts a short algorithm to interact with the sqlite database.

### Other python modules

Additionally to the above modules, the root of the project is made of three core python programs:
- modelisation-2d.py contains the argument parser and the entry point for this project.
- simulation.py constains the functions used to simulate device placement, routing, and serves to test the scripts over a larger deployment (40 devices, 200 applications)
- deployment.py tests for processus and application deployment as a routine called by the other two program. It tests if a device has enough resources to support a given deployment, then tests for bandwidth reservation between deployed processus, and calls the shot between possible and impossible application deployment
