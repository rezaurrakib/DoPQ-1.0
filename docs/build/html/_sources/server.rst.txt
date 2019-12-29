.. raw:: html

    <style> .apicolor{color:#107dac; font-weight: bold; font-style:oblique; font-family:consolas } </style>
	<style> .apicolor1{color:#107dac; font-weight: bold; font-family:consolas} </style>
	<style> .attentiontext{color:red; font-weight: bold;} </style>

.. role:: apicolor1

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
-------------------------


docker_helper Package
----------------------


utils Package
-------------


provider.py
-----------


docker_pq_model.py
-------------------


data_platform.py
-----------------


model_helper.py
----------------

