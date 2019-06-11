import sys, os, time
from pyqt_interface import css_layout
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow, QWidget, QListWidget, QTextEdit, QApplication
from PyQt5.QtWidgets import QDockWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QIcon, QFont, QPixmap
from utils import log

from pyqt_interface import qt_display_process

LOG = log.get_module_log(__name__)

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        title = "DockAble Application"

        self.main_window_screen_resize()
        self.main_window_layout()

        self.textEdit = QTextEdit()
        self.setCentralWidget(None)

        # Initialize SubWindow variables. All are QDockWidget object
        self.status_dock = None
        self.user_stats_dock = None
        self.running_containers_dock = None
        self.enqueued_dock = None
        self.history_dock = None
        self.initialize_subwindows()

    # Load the sub windows for the first time
    def initialize_subwindows(self):
        # self.dock_header()
        self.status_dock = self.dock_status()
        self.user_stats_dock = self.dock_userstats()
        self.running_containers_dock = self.dock_running_continers()
        self.enqueued_dock = self.dock_enqueued_containers()
        self.history_dock = self.dock_history()

        return [self.status_dock, self.user_stats_dock, self.running_containers_dock,
                self.enqueued_dock, self.history_dock]


    def main_window_screen_resize(self):
        self.showMaximized()
        #self.setWindowState(QtCore.Qt.WindowMaximized)
        self.setWindowTitle("  DopQ LMU AugenKlinik")

    def main_window_layout(self):
        self.setStyleSheet(css_layout.main_window_layout)


    def subdoc_font_customization(self):
        current_font = self.font()
        current_font.setBold(True)
        current_font.setPixelSize(25)
        current_font.setFamily("")

        return current_font

    def subdoc_custom_title_bar(self, subwin_name):
        label = None

        if subwin_name == "userstats":
            label = QLabel("                                                     ~~~ User Statistics ~~~"
                           "\n                                                     ----------------------------------")
            label.setStyleSheet(css_layout.userstats_title_bar)

        elif subwin_name == "status":
            label = QLabel("                                                     ~~~ Status ~~~"
                           "\n                                                     -----------------------")
            label.setStyleSheet(css_layout.status_title_bar)

        elif subwin_name == "running":
            label = QLabel("                                             ~~~ Running Containers ~~~"
                           "\n                                             -----------------------------------------")
            label.setStyleSheet(css_layout.running_cont_title_bar)

        elif subwin_name == "enqueued":
            label = QLabel("                                             ~~~ Enqueued Containers ~~~"
                           "\n                                             -------------------------------------------")
            label.setStyleSheet(css_layout.enqueued_cont_title_bar)

        elif subwin_name == "history":
            label = QLabel("                                                  ~~~ History ~~~"
                           "\n                                                  ------------------------")
            label.setStyleSheet(css_layout.history_title_bar)


        return label

    def screen_geometry_details(self):
        screenGeometry = QApplication.desktop()
        rect = screenGeometry.availableGeometry()
        print("Screen_width: ", rect.width())
        print("Screen_Height: ", rect.height())
        return rect.height(), rect.width()

    """
        Definition of the Main Window Header
        HBoxLayout can be used ....
    """

    def dock_header(self):
        dock = QDockWidget(self)
        dock.setTitleBarWidget(self.subdoc_custom_title_bar("header"))
        dock.setFeatures(dock.NoDockWidgetFeatures)
        height, width = self.screen_geometry_details()
        dock.setFixedWidth(width)
        dock.setFixedHeight(height * 15 // 100 ) # 10% of total height

        dock.setStyleSheet(css_layout.dockwidget_main_header_layout)

        #vbox = QHBoxLayout()

        l1 = QLabel()
        #l1.setStyleSheet(css_layout.main_header_label_layout)
        #w = l1.width()
        #h = l1.height()
        #print("w, h: ", w, h)

        l1.setWordWrap(True)
        l1.setText("DopQ : Docker Priority Queue")
        l1.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap("../asset_files/images.png")
        l1.setPixmap(pixmap)
        #l1.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))
        l1.setMinimumHeight(pixmap.height())
        dock.setWidget(l1)

        self.addDockWidget(Qt.TopDockWidgetArea, dock)


    """
        Definition of the status sub-window
    """

    def dock_status(self):
        dock = QDockWidget(self)
        #dock.setWindowTitle("~~~ Current Status ~~~")
        dock.setTitleBarWidget(self.subdoc_custom_title_bar("status"))
        dock.setFont(self.subdoc_font_customization())
        dock.setFeatures(dock.NoDockWidgetFeatures)

        height, width = self.screen_geometry_details()
        dock.setFixedWidth(width//2)
        dock.setFixedHeight((height * 3)//10 - 10) # 30% of total height

        dock.setStyleSheet(css_layout.dockwidget_layout)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.data = [""]

        self.listwidget = QListWidget(dock)
        self.listwidget.addItems(self.data)
        dock.setWidget(self.listwidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        return dock

    """
        Definition of the User-Status sub-window
    """

    def dock_userstats(self):
        dock = QDockWidget(self)
        #dock.setWindowTitle("~~~ User Statistics ~~~")
        dock.setTitleBarWidget(self.subdoc_custom_title_bar("userstats"))
        dock.setFont(self.subdoc_font_customization())
        dock.setFeatures(dock.NoDockWidgetFeatures)

        height, width = self.screen_geometry_details()
        dock.setFixedWidth(width//2)
        dock.setFixedHeight(height//5 - 10) # 1/5th of total height

        dock.setStyleSheet(css_layout.dockwidget_layout)

        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.data = [""]

        self.listwidget = QListWidget(dock)
        self.listwidget.addItems(self.data)
        dock.setWidget(self.listwidget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        return dock

    """
        Definition of the Runinng Container sub-window
    """

    def dock_running_continers(self):
        dock = QDockWidget(self)
        #dock.setWindowTitle("~~~ Running Containers ~~~")
        dock.setTitleBarWidget(self.subdoc_custom_title_bar("running"))
        dock.setFont(self.subdoc_font_customization())
        dock.setFeatures(dock.NoDockWidgetFeatures)

        height, width = self.screen_geometry_details()
        dock.setFixedWidth(width//2)
        dock.setFixedHeight((height*7)//10 - 20) # 70% of the height

        dock.setStyleSheet(css_layout.dockwidget_layout)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.data = [""]

        self.listwidget = QListWidget(dock)
        self.listwidget.addItems(self.data)
        dock.setWidget(self.listwidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        return dock


    """
        Definition of the Enqueued Container sub-window
    """

    def dock_enqueued_containers(self):
        dock = QDockWidget(self)
        #dock.setWindowTitle("~~~ Enqueued Containers ~~~")
        dock.setTitleBarWidget(self.subdoc_custom_title_bar("enqueued"))
        dock.setFont(self.subdoc_font_customization())
        dock.setFeatures(dock.NoDockWidgetFeatures)

        height, width = self.screen_geometry_details()
        dock.setFixedWidth(width // 2)
        dock.setFixedHeight((height//5) * 2 - 12)

        dock.setStyleSheet(css_layout.dockwidget_layout)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.data = [""]

        self.listwidget = QListWidget(dock)
        self.listwidget.addItems(self.data)
        dock.setWidget(self.listwidget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        return dock

    """
        Definition of the History sub-window
    """

    def dock_history(self):
        dock = QDockWidget(self)
        #dock.setWindowTitle("~~~ History ~~~")
        dock.setTitleBarWidget(self.subdoc_custom_title_bar("history"))
        dock.setFont(self.subdoc_font_customization())
        dock.setFeatures(dock.NoDockWidgetFeatures)

        height, width = self.screen_geometry_details()
        dock.setFixedWidth(width // 2)
        dock.setFixedHeight((height//5) * 2 - 12)

        dock.setStyleSheet(css_layout.dockwidget_layout)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.data = [""]

        self.listwidget = QListWidget(dock)
        self.listwidget.addItems(self.data)
        dock.setWidget(self.listwidget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        return dock


'''
# This class is for updating subwindow with DopQ Information

class SubWinUpdate(Window):
    def __init__(self):
        super(SubWinUpdate, self).__init__()

    # Function for updating dock widgets
    # Data sent from QThread using signal

    def update_status_widget_from_thread_test(self, data):
        print("call is in update_widget_from_thread_test ")
        list_widget = self.status_dock.widget()
        final_string = "Status Entry:\n---------------\n"
        for key, val in data.items():
            if (key == "provider status"):
                final_string += "\n"

            final_string += key + " : " + val
            final_string += " | "
        final_string += "\n"
        list_widget.addItems([final_string])
        self.status_dock.setWidget(list_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.status_dock)

    def update_enqueue_widget_from_thread_test(self, data):
        print("call is in update_widget_from_thread_test ")
        list_widget = self.enqueued_dock.widget()
        final_string = "Enqueued Containers Entry:\n--------------------------------\n"
        for key, val in data.items():
            if (key == "provider status"):
                final_string += "\n"

            final_string += key + " : " + val
            final_string += " | "

        final_string += "\n"
        list_widget.addItems([final_string])
        self.enqueued_dock.setWidget(list_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.enqueued_dock)

    def update_runnning_widget_from_thread_test(self, data):
        print("call is in update_widget_from_thread_test ")
        list_widget = self.running_containers_dock.widget()
        print(self.running_containers_dock)
        final_string = "Running Containers Entry:\n------------------------------\n"
        for key, val in data.items():
            if (key == "provider status"):
                final_string += "\n"

            final_string += key + " : " + val
            final_string += " | "

        final_string += "\n"
        list_widget.addItems([final_string])
        self.running_containers_dock.setWidget(list_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.running_containers_dock)

    def signal_passing_test(self):
        print("call is in signal_passing_test ")
        self.test_thread = qt_display_process.QThreadWorker()
        self.test_thread.sig1.connect(self.update_status_widget_from_thread_test)
        self.test_thread.sig2.connect(self.update_runnning_widget_from_thread_test)
        self.test_thread.sig3.connect(self.update_enqueue_widget_from_thread_test)

        self.test_thread.start()
    '''


class SubWindow(Window):
    def __init__(self, parent, func, dockwidget):
        super(SubWindow, self).__init__()
        self.parent = parent
        self.screen = dockwidget

        if isinstance(func, type):
            LOG.info('Command is in: {}'.format("isinstance method in SubWindow class"))
            LOG.info('Command is in: {}'.format("DopQ Status: "  + self.parent.dopq.status))
            print("It has entered in the isinstance method")
            self.func = func(self, self.parent.dopq)

        else:
            #time.sleep(15)
            LOG.info('Command is in: {}'.format("Display function call in SubWindow class"))
            self.func = DisplayFunction(self, self.parent.dopq)

        #self.status_dock = self.subwindow_status()

    def __call__(self, *args, **kwargs):
        """
        execute self.func when this object is called
        :param args:
        :param kwargs:
        :return:
        """
        return self.func(*self.args, **kwargs)


    def subwindow_display_update(self, dock, data):
        """
        Probably the most important function ...
        I'm still not sure how to make this API run. Need to think a lot.
        """
        list_widget = dock.widget()
        text = [self.string_creation(data)]

        list_widget.addItems(text)
        dock.setWidget(list_widget)

        return dock

    def string_creation(self, data):
        final_str = ""
        for key, value in list(data.items()):
            final_str += key
            final_str += ": "
            final_str += value
            final_str += "\n"

        return final_str

    '''
    def subdoc_custom_title_bar(self):
        label = QLabel("                                     ~~~ Status ~~~"
                       "\n                                   ---------------")
        label.setStyleSheet(css_layout.userstats_title_bar)
        return label

    def subwindow_status(self):
        dock = QDockWidget(self)
        dock.setWindowTitle("~~~ Current Status ~~~")
        dock.setTitleBarWidget(self.subdoc_custom_title_bar())
        dock.setFont(self.subdoc_font_customization())
        dock.setFeatures(dock.NoDockWidgetFeatures)

        height, width = self.screen_geometry_details()
        dock.setFixedWidth(width//2)
        dock.setFixedHeight(height//2 - 10)

        dock.setStyleSheet(css_layout.dockwidget_layout)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.data = ["Entry 1", "======================\nRexa", "Pear", "Banana",
                        "App", "Melon", "Pear", "Banana",
                        "App", "Melon", "Pear", "Banana",
                        "App", "hfdjh", "Pear", "Banana",
                        "Entry 2", "======================", "Pear", "Banana",
                        "App", "Melon", "shetw", "Banana",
                        "dhfjhd", "sdh", "Pear", "erere"]

        self.listwidget = QListWidget(dock)
        self.listwidget.addItems(self.data)
        dock.setWidget(self.listwidget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        return dock

    def update_doc(self, dock):
        list_widget = dock.widget()
        self.data = ["Updated Entry", "======================\nMikayla", "Markus", "Banana",
                     "App", "Melon", "Pear", "Banana",
                     "App", "Melon", "Pear", "Banana",
                     "App", "hfdjh", "Pear", "Banana"]
        list_widget.addItems(self.data)
        dock.setWidget(list_widget)
        
        #self.addDockWidget(Qt.RightDockWidgetArea, dock)
        return dock
    '''


"""
    >> The Base/Parent class for Displaying Information 
    >> Other Display Classes should be updated through this class 
"""


class DisplayFunction(object):
    def __init__(self, subwindow, dopq):
        self.first_call = True
        self.displayed_information = None
        self.fields = {}
        self.dopq = dopq
        self.dockwidget = subwindow

    def __call__(self, *args, **kwargs):
        """
        write template to screen if its the first time calling this class, then update the information in the template
        :param args: not used
        :param kwargs: not used
        :return: None
        """

        if self.first_call:
            self.reset_displayed_information()
            self.load_template()
            self.update_info()
        else:
            self.update_info()


    # This API should be implemented by the child classes
    def update_info(self):
        """
        update displayed information
        :return: None
        """
        raise NotImplementedError('abstract method')

    # This API should be implemented by the child classes
    def load_template(self):
        """
        write template to display on first function call
        :return: None
        """
        raise NotImplementedError('abstract method')

    def update_dock_content(self, data):
        """
        :param data: A Dictionary containing information about the fields
        :return:
        """
        self.dockwidget.screen = self.dockwidget.subwindow_display_update(self.dockwidget.screen, data)


    def reset_displayed_information(self):
        for index, info in enumerate(self.displayed_information):
            if isinstance(info, str):
                self.displayed_information[info] = ''
            else:
                for field in list(info.keys()):
                    self.displayed_information[index][field] = ''




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    app.setStyle("Fusion")
    mainWin = SubWinUpdate()
    mainWin.show()
    mainWin.signal_passing_test()

    sys.exit(app.exec_())