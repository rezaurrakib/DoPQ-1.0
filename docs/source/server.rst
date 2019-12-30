.. raw:: html

    <style> .apicolor{color:#107dac; font-weight: bold; font-style:oblique; font-family:consolas } </style>
	<style> .apicolor1{color:#107dac; font-weight: bold; font-family:consolas} </style>
	<style> .attentiontext{color:blue; font-weight: bold;} </style>
	<style> .attentiontext1{color:#107dac; font-weight: bold;} </style>
	

.. role:: apicolor1

.. role:: attentiontext

.. role:: attentiontext1


Server Code
===========
DoPQ server is a python package that contains two different processes run independently, **Provider** class which is a spawning process that provides  
process-based “threading” interface and a **DopQContainer** class that provides Thread-based parallelism. As the whole DoPQ system has been built on MVC pattern, 
the server consists of the model and the controller module. The **DopqController** class is exposed by the Pyro4 library and provides a series of public APIs for 
communicating remotely with the client processes.    

In the server part, there are a lot of stuffs going under the hood. Several python classes are written for running all the processes and building docker images and containers. 
We will discuss them briefly in this section.

Controller and Wrapper
-----------------------
* :ref:`controller.py`
* :ref:`data_platform.py`

Utility Packages
----------------
* :ref:`container_handler Package`
* :ref:`docker_helper Package`
* :ref:`utils Package`

Provider and Queue Classes
---------------------------
* :ref:`provider.py`
* :ref:`docker_pq_model.py`
* :ref:`model_helper.py`

controller.py
--------------
*class* **DopqController()**

	This class is the gateway for communicating with the provider and priority queue processes.
	It initiates the execution of server processes by invoking the instances of **Provider()**
	and **DopQContainer()** classes. From here, the remote connection daemon thread is also 
	started by invoking *Pyro4.Daemon()*. Through this daemon, client thread communicates with the server.
	
.. code-block:: python

    def remote_connection_starter(self, dp_obj):
        #Pyro4.config.HOST = "10.167.183.156" # dopq_server ip as host
        #Pyro4.config.NS_PORT = 9090
        self.server_deamon = Pyro4.Daemon()
        nameserver = Pyro4.locateNS()
        uri = self.server_deamon.register(self)
        nameserver.register("remote_dopq", uri)
        print("Server URI is : ", uri)
        self.server_deamon.requestLoop()

DopqController() provides a series of APIs to send information and receive commands from client side. 
The APIs are :

	- :attentiontext1:`get_running_containers_info()`
	- :attentiontext1:`get_containers_history_info()`
	- :attentiontext1:`get_enqueued_containers_info()`
	- :attentiontext1:`get_dopq_system_status()`
	- :attentiontext1:`get_dopq_user_statistics()`
	- :attentiontext1:`delete_req_enqueued_containers()`
	- :attentiontext1:`dopq_system_lock()`
	- :attentiontext1:`clear_dopq_history()`
	- :attentiontext1:`shutdown_queue()`
		
data_platform.py
-----------------
*class* **DataPlatform()**
	
	It's a wrapper class for controller to delegate commands to the processes and fetch information from
	the processes as well. Exposed by the Pyro4 library. A list of shared variables defined in the 
	*DopQContainer()* class in the **docker_pq_model.py** file are updated when the queue thread is running.
	From the *DataPlatform()* class, several delegate methods are defined, through which these shared variables 
	can be accessed. 
	
	Some important APIs are:
	
	- :attentiontext1:`get_running_info()`
	- :attentiontext1:`get_user_statistics()`
	- :attentiontext1:`get_dopq_status()`
	- :attentiontext1:`get_completed_containers_info()`
	- :attentiontext1:`get_enqueued_container_list()`
	- :attentiontext1:`exec_dopq_lock_state()`
	- :attentiontext1:`update_enqueued_container_list()`
	- :attentiontext1:`clear_dopq_history_list()`
		

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
*class* **DopQContainer()** 

	Constructs a class based on higher level threading interface for parallel processing of docker containers build by the provider process.
	It maintains a multiprocessing Queue that is updated when a Provider instance find new zip file, build a docker container from that and 
	finally put that container on the queue. Three difference list is updated in this class.
	
	- :apicolor1:`running_container` (Trace the currently running containers on the GPU/Machine.)
	- :apicolor1:`containers_list` (Contain the containers who are currently on the Queue.)
	- :apicolor1:`history` (Have all the completed containers info.)
	
	:apicolor1:`start_dopq_process()`
		Register the container queue as a threading object.
		
.. code-block:: python

    def start_dopq_process(self
        self.process_starttime()
        self.dopq_process = threading.Thread(target=self.exec_dopq_process)
        self.dopq_process.start()		


:apicolor1:`exec_dopq_process()`
	This private API is launched in a separate process invoked by threading module. Runs parallelly with the provider process.
	Infinitely Checks for a new docker container from the provider process.	
	
model_helper.py
----------------
*class* **ModelHelper()**
	
	This is a helper class for DoPQ model. Contains several static methods for building the **config.ini** file, read the users list from db etc.
	
	:apicolor1:`write_default_config()`
		Write the default configuration. Set the container build *paths*, docker configuration, queue configuration etc.
		
	:apicolor1:`parse_config()`
		Create config parser and read from **config.ini** file.
		
	:apicolor1:`split_and_calc_penalty()`
		Method invoked for calculating penalty score for every user who runs docker container in the system. There are a series of APIs doing this task.
		For more details, please look into *model_helper.py* file.
	
	:apicolor1:`container_freq_for_user()`
		Helper method for counting how many containers in the list belong to a valid user.

