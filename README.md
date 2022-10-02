# Fuspaq
Fuspaq is a platform that integrates with FaaS platforms to allow applications to adjust QoS parameters based on alternative service implementations or its configuration settings.
This is a project of the University of Málaga (Spain).

# Requirements

- A FaaS framework running (configure gateway url and port in server.py)
- Python (https://www.python.org/).
- Z3 solver for Python (https://pypi.org/project/z3-solver/).

# Usage

run:  python fuspaq.py repository model objective

Where repository and model are json files containing the list of implemented functions and parameters, and the workflow of the application, respectively; and objective is the optimization objective (e.g. mincost).

When running, the platform is ready to accept serverless function calls the same way as with the FaaS framework, by doing REST requests to the fuspaq port (by default 8081, configurable at server.py).
Objectives and optimization constraints can be introduced at runtime using qos requests' port (by default 8082) (see server.py for implemented options, e.g. objective=mintime). This requests will relaunch optimization process automatically.
