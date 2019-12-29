.. raw:: html

    <style> .apicolor{color:#107dac; font-weight: bold; font-style:oblique; font-family:consolas } </style>
	<style> .apicolor1{color:#107dac; font-weight: bold; font-family:consolas} </style>
	<style> .attentiontext{color:blue; font-weight: bold;} </style>

.. role:: apicolor1

.. role:: attentiontext

Server Code
===========
DoPQ server is a python package that contains two different processes run independently, **Provider** class which is a spawning process that provides  
process-based “threading” interface and a **DopQContainer** class that provides Thread-based parallelism. As the whole DoPQ system has been built on MVC pattern, 
the server consists of the model and the controller module. The **DopqController** class is exposed by the Pyro4 library and provides a series of public APIs for 
communicating remotely with the client processes.    

In the server part, there are a lot of stuffs going under the hood. Several python classes are written for running all the processes and building docker images and containers. 
We will discuss them briefly in this section.

Utility Packages
----------------
* :ref:`container_handler Package`
* :ref:`docker_helper Package`
* :ref:`utils Package`

Python Source Files
-------------------
* :ref:`provider.py`
* :ref:`docker_pq_model.py`
* :ref:`data_platform.py`
* :ref:`model_helper.py`


container_handler Package
--------------------------

This package consists of two files.

 - :attentiontext:`container.py`
 - :attentiontext:`container_config.py`
 

container_config.py
--------------------

*class* **ContainerConfig()** 

	This class sets the configuration for every docker container objects. It mainly sets a docker container's:
	
		- Name
		- Executor(User) of the container
		- Required memory to run a container
		- Number of GPUs
		- How many slots are needed
		- Set the build flag etc.


container.py
-------------
A wrapper for docker container objects. When invokes, creates a new container instance. 

.. Note:: It takes two params. 
	
	- *config* : Provides a running configuration for the docker container.
	- *container_obj*: The underlying docker container instance.

	It has a method called *exec_run()*, which is for running a command inside the docker container. This is similar to *docker_exec*. The function definition is as follows:
	
.. code-block:: python

	def exec_run(self, cmd, stdout=True, stderr=True, stdin=False, tty=False,
                 privileged=False, user='', detach=False, stream=False,
                 socket=False, environment=None):
				 
If you wanna know more details about this, Have a look into `Docker SDK for Python <https://docker-py.readthedocs.io/en/stable/containers.html>`_.
		
docker_helper Package
----------------------
A helper package to unzip the zipped folders, load and build the docker images from docker configuration file, and finally build the docker container. It contains the following files:
	
	- :attentiontext:`docker_build.py`
	- :attentiontext:`docker_fetch.py`
	- :attentiontext:`docker_parser.py`


utils Package
-------------
Utils package contains helper classes for calculating GPU and CPU usage percentage and monitoring hardware and GPU minors. 
Also a customized class for writing logs of queue and provider processes updates. Contains following files:
	
	- :attentiontext:`cpu.py`
	- :attentiontext:`gpu.py`
	- :attentiontext:`log.py`

provider.py
-----------

*class* **Provider()**
Provider class is a python multiprocess. This class is designed for handling zipped docker files provided by the user to run on the DoPQ server. 

	:apicolor1:`monitoring_provider()`
		A process based thread running continuously to fetch zipped files from shared network to local machine, unzip that, then build the docker images and 
		create the docker container. After building the docker container, it puts that into a priority queue.


docker_pq_model.py
-------------------


data_platform.py
-----------------


model_helper.py
----------------

