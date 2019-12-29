.. raw:: html

    <style> .apicolor{color:#107dac; font-weight: bold; font-style:oblique; font-family:consolas } </style>
	<style> .apicolor1{color:#107dac; font-weight: bold; font-family:consolas} </style>
	<style> .attentiontext{color:red; font-weight: bold;} </style>

.. role:: apicolor1

Client Code
===========
DoPQ client is a python package that supports APIs for fethcing data from remote server by exploiting Pyro4 remote server object. There are several python classes each responsible for specific tasks about this communication process. We will discuss them briefly in this section.


* :ref:`dopq_client.py`
* :ref:`view_thread.py`
* :ref:`interface_pipeline.py`
* :ref:`parent_window.py`

dopq_client.py
--------------

*class* **Client** (Object)

	A python class for initiating the process of locating the Pyro4 Name Server and establish connection between remote server and client.
	
	:apicolor1:`deamon_creation()`
		Method for locating the Name Server and get the server URI. Using that URI, the remote server object is detected.
	
	:apicolor1:`view_thread_communicator(dopq_server_obj)` 
	    Send the remote server object to the interface_pipeline for passing it to the QThread class.
	


view_thread.py
--------------

*class* **QThreadWorker** (QThread)
	
	A QThread class for invoking remote APIs from the server through the remote server object, send from the *Client* class. 
	
	:apicolor1:`run()`
		Method representing the QThread's activity. It invokes the following methods to get the server information.
	
	:apicolor1:`fetch_running_containers_info()`
		A client side getter method for fetching information about currently running docker containers in the DoPQ process.
	
	:apicolor1:`fetch_enqueued_containers_info()`
		Getter method for fetching the enqueued docker containers information.

	:apicolor1:`fetch_user_stats()`
		Fetch the user statistics of the DoPQ system  
		
	:apicolor1:`fetch_history_info()`
		Getter method for fetching the docker containers history.
	
	:apicolor1:`fetch_status_info()`
		Method for collecting Queue and Provider process status and start time from server.
	
	The above APIs are the initial container for the information send from the server. Using the pyqtSignal class, these information are then emitted in the :apicolor1:`run()` method.
	
	
	

parent_window.py
----------------
*class* **ParentWindow** (QMainWindow)
	
	A python class for creating the GUI using PyQt5 framework. It inherits the QMainWindow class and define the sub windows as `QMdiArea <https://doc.qt.io/qt-5/qmdiarea.html#details>`_  class objects from PyQt5. 

	:apicolor1:`screen_geometry_details()`
		Method for calculating the display screen's total height and width.
		
	:apicolor1:`parent_window_layout()`
		Method for setting the layout for the parent window.
	
	:apicolor1:`init_status_dockwidget()`
		Returns a QDockWidget object for the status sub window. The layout of the QDockWidget object is defined here.
	
	:apicolor1:`create_dopq_stat_subwindow()`
		Initialized for creating the DoPQ status sub window using **QMdiArea** object. From this method :apicolor1:`init_status_dockwidget()` is invoked and the returned 
		QDockWidget is set on the **QMdiSubWindow()** object. The QMdiSubWindow() object later added as a sub window in the QMdiArea. See the following code snippet for more details. 	
	
	.. code-block:: python
          
          def create_userstat_subwindow(self):
              """
              Summary of the function:
              ------------------------
              (a) Prepare the DoPQ User Status Subwindow.
              (b) Contains the user stat. dock widget inside the QMdiSubWindow

              Parameters:
              -----------
              :arg: None
              :return: None
              """
              self.user_stats_dock = self.userstats_subwindow()
              self.user_stat_subwin = QMdiSubWindow()
              self.user_stat_subwin.setWindowTitle("User Status")
              self.user_stat_subwin.setFixedHeight((int(self.screen_height * 3.4) // 10))  # 34%
              self.user_stat_subwin.setFixedWidth(self.screen_width // 2)
              self.user_stat_subwin.setWidget(self.user_stats_dock)
              self.user_stat_subwin.setMouseTracking(False)
              self.user_stat_subwin.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
              self.user_stat_subwin.move(0, (int(self.screen_height * 2.11) // 10))
              self.mdi.addSubWindow(self.user_stat_subwin)
			
		
	
	:apicolor1:`init_userstats_dockwidget()`
		Returns a QDockWidget object for creating a QMdiArea sub window in order to show user statistics.
		
	:apicolor1:`create_userstats_subwindow()`
		Initialized for creating a QMdiArea sub window for the user status. Invoked the method :apicolor1:`init_userstats_dockwidget()` and load the QMdiSubWindow() object with the returned QDockWidget object.	

	:apicolor1:`init_running_cont_dockwidget()`
		Returns a QDockWidget object for running containers sub window.
		
	:apicolor1:`create_running_cont_subwindow()`
		Invokes :apicolor1:`init_running_cont_dockwidget()` and load the QMdiArea object with the dock widget returned from that method.
		
	:apicolor1:`init_enqueued_cont_dockwidget()`
		Returns a QDockWidget object for enqueued docker containers sub window.
		
	:apicolor1:`create_enqueued_cont_subwindow()`
		Invokes :apicolor1:`init_enqueued_cont_dockwidget()` and load the QMdiArea object with the dock widget returned from that method.
		
	:apicolor1:`init_history_dockwidget()`
		Returns a QDockWidget object for showing previously completed docker containers history.
		
	:apicolor1:`create_history_subwindow()`
		Invokes :apicolor1:`init_history_dockwidget()` and load the QMdiArea object with the dock widget returned from that method.


	
interface_pipeline.py
---------------------
.. role:: attentiontext

:apicolor1:`qt_main()`
	From this API, the PyQt user interface is launched. It creates an interface object and loads the initial UI. Then it invokes the :apicolor1:`thread_connector()` API 
	from the **InterfacePyQt** class in order to connect the signals emitted from the :apicolor1:`run()` method of **QThreadWorker** class.  

*class* **InterfacePyQt** (ParentWindow)
	
	:apicolor1:`dock_main_menu()`
		Creating the main menu bar of the DoPQ GUI. Returns a list of menu.    
		
	:apicolor1:`submenu_command_options()`
		Method defines the options in the 'Commands' Menu. These are the set of commands initiate from client PC.
	
	:apicolor1:`onclick_command_update_enqueued_container()`
		Defines the "Enqueued Container Update" command from the "Commands menu". DoPQ process in the server will be :attentiontext:`locked until the update enqueued container is finished`.
		API for locking the DoPQ process invoked in here.

	

