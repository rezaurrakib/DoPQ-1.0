from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow, QWidget, QListWidget, QTextEdit, QApplication

import sys
from  pyqt_interface import qt_display_process
from pyqt_interface.base_window_controller import Window
from PyQt5.QtCore import Qt
from utils import log

LOG = log.get_module_log(__name__)


__authors__ = "Md Rezaur Rahman, Ilja Manakov, Markus Rohm"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Reza, Ilja, Markus"
__status__ = "Dev"


bcolors = {"BLUE": '\033[94m',
           "HIGH": '\033[93m',
           "OKAY": '\033[92m',
           "FAIL": '\033[91m',
           "BOLD": '\033[1m',
           "LINE": '\033[4m',
           "ENDC": '\033[0m'
           }

def green(string):
    return bcolors["OKAY"] + string + bcolors["ENDC"]


def qt_main(dopq):
    app = QtWidgets.QApplication(sys.argv)
    window_obj = InterfacePyQT()
    window_obj.show()
    window_obj.thread_connector(dopq)
    sys.exit(app.exec_())



class InterfacePyQT(Window):
    def __init__(self):
        super(InterfacePyQT, self).__init__()
        #self.dock_widget_list = self.initialize_subwindows()
        #self.dopq = dopq
        #self.subwindows = self.split_screen()

    # Function for updating dock widgets
    # Data sent from QThread using signal

    def update_status_widget_from_thread_test(self, data, isupdate):
        if isupdate:
            final_string = "\n"
            final_string1 = "Queue:       " + data["Queue Status"]
            final_string1 += "\n"
            final_string2 = "                  uptime: " + data["Queue Uptime"] + "         "  + "starttime: " + data["Queue Starttime"]
            final_string2 += "\n\n"
            final_string3 = "Provider:    " + data["Provider Status"]
            final_string3 += "\n"
            final_string4 = "                 uptime: " + data["Provider Uptime"] + "         " + "starttime: " + data["Provider Starttime"]
            final_string4 += "\n"

            list_widget = QListWidget()
            list_widget.addItems([final_string, final_string1, final_string2, final_string3, final_string4])
            list_widget.item(1).setForeground(QtCore.Qt.green)
            list_widget.item(3).setForeground(QtCore.Qt.green)
            self.status_dock.setWidget(list_widget)

        else:
            print("call is in update_widget_from_thread_test ")
            list_widget = self.status_dock.widget()
            final_string = ""
            for key, val in data.items():
                if (key == "Provider Status"):
                    final_string += "\n"

                final_string += key + " : " + val
                final_string += " | "
            final_string += "\n"
            list_widget.addItems([final_string])
            self.status_dock.setWidget(list_widget)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.status_dock)

    def update_enqueue_widget_from_thread_test(self, data):
        print("call is in Enqueued_widget_from_thread_test ")
        list_widget = self.running_containers_dock.widget()
        list_widget = QListWidget()

        for container in data:
            print("Enqueued Container: ", container)
            final_string = "\n"
            final_string += "name:   " + container["name"]  + "                                                            "
            final_string += "status: " + container["status"] + "\n"
            final_string += "--------------------------------------------------------------------------------------------\n"
            final_string += "Docker Name:  " + container['docker name'] + "                                                "
            final_string += "Executor: " + container['executor'] + "\n"
            final_string += "        uptime:  " + container['run_time'] + "                                                "
            final_string += "created: " + container['created'] + "\n\n"
            list_widget.addItems([final_string])

        self.enqueued_dock.setWidget(list_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.enqueued_dock)

    def update_runnning_widget_from_thread_test(self, data):
        print("call is in Running_widget_from_thread_test ")
        list_widget = self.running_containers_dock.widget()
        list_widget = QListWidget()

        for container in data:
            print("container: ", container)
            final_string = "\n"
            final_string += "name:   " + container["name"]  + "                                                   "
            final_string += "status: " + container["status"] + "\n"
            final_string += "-----------------------------------------------------------------------------------\n"
            final_string += "Docker Name:  " + container['docker name'] + "                            "
            final_string += "Executor: " + container['executor'] + "\n"
            final_string += "     uptime:  " + container['run_time'] + "                              "
            final_string += "created: " + container['created'] + "\n"
            final_string += "  cpu usage:  " + container['cpu'] + "                                 "
            if container['memory'] == None:
                final_string += "memory usage:  None" + "\n"
            else:
                final_string += "\n"
            final_string += "  gpu minor:  " + str(container['id'][0]) + "                                 "
            final_string += "  gpu usage" + container['usage'] + "\n"
            list_widget.addItems([final_string])

        self.running_containers_dock.setWidget(list_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.running_containers_dock)

    def thread_connector(self, dopq):
        self.thread_obj = qt_display_process.QThreadWorker(dopq)
        LOG.info('Call is in : {}'.format("thread_connector function"))
        self.thread_obj.sig1.connect(self.update_status_widget_from_thread_test)
        self.thread_obj.sig2.connect(self.update_runnning_widget_from_thread_test)
        self.thread_obj.sig3.connect(self.update_enqueue_widget_from_thread_test)
        self.thread_obj.start()

    def __call__(self, *args, **kwargs):
        """
        infinite loop that displays information and watches for input
        :param args: not used
        :param kwargs: not used
        :return: None
        """
        pass


