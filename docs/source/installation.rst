.. raw:: html

	<style> .attentiontext{color:red; font-weight: bold;} </style>

.. role:: attentiontext

Installation
=============

* :ref:`Requirements`
* :ref:`Start Pyro4 Name Server`
* :ref:`Create User Database`

Requirements
------------
You will need following libraries and frameworks installed in your machine in order to successfully run DoPQ. 

* `PyQt5`_
* `Pyro`_ 4.60+
* `dill`_
* `numpy`_ 
* `GPUtil`_ 
* `datetime`_
* `docker`_ 3.5.0+
* `pickleDB`_ 0.9.2

.. _PyQt5: https://www.riverbankcomputing.com/static/Docs/PyQt5/
.. _Pyro: https://pythonhosted.org/Pyro4/
.. _dill: https://pypi.org/project/dill/
.. _numpy: https://pypi.org/project/numpy/
.. _GPUtil: https://pypi.org/project/GPUtil/
.. _datetime: https://docs.python.org/3.6/library/datetime.html
.. _docker: https://pypi.org/project/docker/
.. _pickleDB: 


Start Pyro4 Name Server
-----------------------
**Pyro4** library has been used in DoPQ application for establishing uninterrupted Inter Process Communication (IPC) between server and client module. The APIs residing in the server side are invoked through a remote object from the client machines through the Pyro4 library. 
 

.. warning:: Pyro4 Nameserver should be started from the server side before running the server process of DoPQ. From the command line terminal, execute the fllowing command:

.. code-block:: bash

   python -m Pyro4.naming -host "HOST_IP" -port "PORT_NO"


Create User Database
---------------------
Before starting the server, you have to configure the user database and set the db path in the configuration settings file. Without this, DoPQ server can't be started.

For registration and user database set-up, please follow the guidelines mentioned in :doc:`Here.<../user registration>`

.. warning:: For setting the db path, update the following lines of the method called *write_default_config()* in the file named **/dopq_server/model/model_helper.py**.

.. code-block:: python

	config.set('paths', 'user_database.dir', 'your_db_path') # In 'write_default_config()' method

.. note:: When the server starts for the first time, it builds a *config.ini* file. This file is used later on for loading the server configuration every time the server starts. This is important to notice that, the *config.ini* file also contains the user information. That's why before starting the server for the first time, one has to redefine the path of the user database from where it reads the username. So, the static method **get_users_db()** needs to be updated in the *model_helper.py* file.

.. code-block:: python

    @staticmethod
    def get_users_db():
        user_db_path = "your_db_path/dopq_database.db" # Put user database path in here
        userlist_str = ""
        db = pickledb.load(user_db_path, False)
        userlist = db.getall()
        for k in userlist:
            userlist_str += k + ","
        userlist_str = userlist_str[:-1]
        return userlist_str


