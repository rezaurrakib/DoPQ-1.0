import client.css_layout as css_layout

from client.utils import log

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QGuiApplication
from PyQt5.QtWidgets import QDockWidget, QLabel, QWidget
from PyQt5.QtWidgets import QToolBar, QAction, QStatusBar, QMainWindow, QMdiArea, QMdiSubWindow

LOG = log.get_module_log(__name__)

__authors__ = "Md Rezaur Rahman"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Reza, Ilja, Markus"
__status__ = "Dev"


class ParentWindow(QMainWindow):
    def __init__(self):
        super(ParentWindow, self).__init__()
        self.main_window_maximized()
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.parent_window_layout()
        self.setWindowTitle("Docker Priority Queue - [DoPQ::Version - 1.2]")
        self.screen_height, self.screen_width = self.screen_geometry_details()

        # Initialize Dock Widget variables. It is used as a container, hold a listwidget for displaying information
        self.header_dock = None
        self.dopq_stat_dock = None
        self.user_stats_dock = None
        self.running_containers_dock = None
        self.enqueued_dock = None
        self.history_dock = None
        self.init_subwindows()

        # Init QMdiSubWindow variables. Each contains a QDockWidget and show/update information coming from dopq_server
        self.dopq_stat_subwin = None
        self.user_stat_subwin = None
        self.running_subwin = None
        self.enqueued_subwin = None
        self.history_subwin = None

    def main_window_maximized(self):
        """
        Summary of the function:
        ------------------------
        (a) Set the parent window size , default: full screen

        Parameters:
        -----------
        :arg: None
        :return: None
        """
        self.showMaximized()

    def parent_window_layout(self):
        """
        Summary of the function:
        ------------------------
        (a) Set the layout for the parent window

        Parameters:
        -----------
        :arg: None
        :return: None
        """
        self.setStyleSheet(css_layout.main_window_layout)

    @staticmethod
    def screen_geometry_details():
        """
        Summary of the function:
        ------------------------
        (a) Calculate the display screen's total height and width

        Parameters:
        -----------
        :arg: None
        :return: Screen's {height, width} as a pair
        """
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        h = screen_geometry.height()
        w = screen_geometry.width()
        print("Screen_width New: ", w)
        print("Screen_Height New: ", h)
        return h, w

    def init_subwindows(self):
        self.create_dopq_stat_subwindow()
        self.create_userstat_subwindow()
        self.create_history_subwindow()
        self.create_running_subwindow()
        self.create_enqueued_subwindow()

    def create_dopq_stat_subwindow(self):
        """
        Summary of the function:
        ------------------------
        (a) Prepare the DoPQ Status Subwindow.
        (b) Contains the status dock widget inside the QMdiSubWindow

        Parameters:
        -----------
        :arg: None
        :return: None
        """
        self.dopq_stat_dock = self.status_subwindow()
        self.dopq_stat_subwin = QMdiSubWindow()
        self.dopq_stat_subwin.setWindowTitle("DoPQ Status")
        self.dopq_stat_subwin.setFixedHeight((int(self.screen_height * 2.1) // 10))  # 21%
        self.dopq_stat_subwin.setFixedWidth(self.screen_width // 2)
        self.dopq_stat_subwin.setWidget(self.dopq_stat_dock)
        self.dopq_stat_subwin.setMouseTracking(False)
        self.dopq_stat_subwin.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.dopq_stat_subwin.move(0, 0)
        self.mdi.addSubWindow(self.dopq_stat_subwin)

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

    def create_history_subwindow(self):
        """
        Summary of the function:
        ------------------------
        (a) Prepare the DoPQ History Subwindow.
        (b) Contains the history dock widget inside the QMdiSubWindow

        Parameters:
        -----------
        :arg: None
        :return: None
        """
        self.history_dock = self.history_subwindow()
        self.history_subwin = QMdiSubWindow()
        self.history_subwin.setWindowTitle("Completed Containers")
        self.history_subwin.setFixedHeight((int(self.screen_height * 3.9) // 10))  # 37%
        self.history_subwin.setFixedWidth(self.screen_width // 2)
        self.history_subwin.setWidget(self.history_dock)
        self.history_subwin.setMouseTracking(False)
        self.history_subwin.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.history_subwin.move(0, (int(self.screen_height * 5.52) // 10))  # Left pan, bottom
        self.mdi.addSubWindow(self.history_subwin)

    def create_running_subwindow(self):
        """
        Summary of the function:
        ------------------------
        (a) Prepare the Running Containers Subwindow.
        (b) Contains the running dock widget inside the QMdiSubWindow

        Parameters:
        -----------
        :arg: None
        :return: None
        """
        self.running_containers_dock = self.running_continers_subwindow()
        self.running_subwin = QMdiSubWindow()
        self.running_subwin.setWindowTitle("Running Containers")
        self.running_subwin.setFixedHeight((int(self.screen_height * 4.8) // 10))  # 48%
        self.running_subwin.setFixedWidth(int(self.screen_width * 4.97) // 10)
        self.running_subwin.setWidget(self.running_containers_dock)
        self.running_subwin.setMouseTracking(False)
        self.running_subwin.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.running_subwin.move(int(self.screen_width * 5.01) // 10, 0)  # Right pan, top
        self.mdi.addSubWindow(self.running_subwin)

    def create_enqueued_subwindow(self):
        """
        Summary of the function:
        ------------------------
        (a) Prepare the Enqueued Subwindow.
        (b) Contains the enqueued dock widget inside the QMdiSubWindow

        Parameters:
        -----------
        :arg: None
        :return: None
        """
        self.enqueued_dock = self.enqueued_containers_subwindow()
        self.enqueued_subwin = QMdiSubWindow()
        self.enqueued_subwin.setWindowTitle("Enqueued Containers")
        self.enqueued_subwin.setFixedHeight((int(self.screen_height * 4.6) // 10))  # 48%
        self.enqueued_subwin.setFixedWidth(int(self.screen_width * 4.97) // 10)
        self.enqueued_subwin.setWidget(self.enqueued_dock)
        self.enqueued_subwin.setMouseTracking(False)
        self.enqueued_subwin.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.enqueued_subwin.move(int(self.screen_width * 5.01) // 10, (int(self.screen_height * 4.81) // 10))  # Right pan, bottom
        self.mdi.addSubWindow(self.enqueued_subwin)

    @staticmethod
    def subdoc_custom_title_bar(subwin_name):
        """
        Summary of the function:
        ------------------------
        (a) Prepare the title bar for the specific dock widget.

        Parameters:
        -----------
        :subwin_name: str
            The name of the dock_widget
        :return: QLabel object
            The label(With str) for the specific dock widget title bar
        """
        label = QLabel()

        if subwin_name == "userstats":
            label.setText(css_layout.USER_STAT_TITLE_HTML)
            label.setAlignment(Qt.AlignCenter)
            new_font = QFont("Lucida Console", 15, QFont.Bold)
            label.setFont(new_font)
            label.adjustSize()
            label.setStyleSheet(css_layout.userstats_title_bar)

        elif subwin_name == "status":
            label.setText(css_layout.STATUS_TITLE_HTML)
            label.setAlignment(Qt.AlignCenter)
            new_font = QFont("Courgette", 15, QFont.Bold)
            label.setFont(new_font)
            label.adjustSize()
            label.setStyleSheet(css_layout.status_title_bar)

        elif subwin_name == "running":
            label.setText(css_layout.RUNNING_CONT_TITLE_HTML)
            label.setAlignment(Qt.AlignCenter)
            new_font = QFont("Courgette", 15, QFont.Bold)
            label.setFont(new_font)
            label.adjustSize()
            label.setStyleSheet(css_layout.running_cont_title_bar)

        elif subwin_name == "enqueued":
            label.setText(css_layout.ENQUEUED_CONT_TITLE_HTML)
            label.setAlignment(Qt.AlignCenter)
            new_font = QFont("Courgette", 15, QFont.Bold)
            label.setFont(new_font)
            label.adjustSize()
            label.setStyleSheet(css_layout.enqueued_cont_title_bar)

        elif subwin_name == "history":
            label.setText(css_layout.HISTORY_TITLE_HTML)
            label.setAlignment(Qt.AlignCenter)
            new_font = QFont("Courgette", 15, QFont.Bold)
            label.setFont(new_font)
            label.adjustSize()
            label.setStyleSheet(css_layout.history_title_bar)

        return label

    def subdoc_font_customization(self):
        """
        Summary of the function:
        ------------------------
        (a) Font customization for the sub-window/dock-widget

        Parameters:
        -----------
        :arg: None
        :return: A QFont object
        """
        current_font = self.font()
        current_font.setBold(True)
        current_font.setPixelSize(25)
        current_font.setFamily("")
        return current_font

    ################################ Sub Windows ################################
    # Five APIs -> Dock Widget creation for displaying docker containers info   #
    # Initially load with null data.                                            #
    # All dock widget objects contain a list widget to show data                #
    #############################################################################

    def dock_main_menu(self):
        self.menuBar().setStyleSheet("QMenuBar::item { color: rgb(255, 255, 255); }")
        main_menu = self.menuBar()

        file_menu = main_menu.addMenu('DoPQ-Arena')
        file_menu.setStyleSheet("QMenu::item { color: rgb(255, 255, 255); }")

        commands_menu = main_menu.addMenu('Commands')
        commands_menu.setStyleSheet("QMenu::item { color: rgb(255, 255, 255); }")

        viewMenu = main_menu.addMenu('View')
        searchMenu = main_menu.addMenu('Search')
        toolsMenu = main_menu.addMenu('Tools')
        helpMenu = main_menu.addMenu('About DoPQ')

        new_action = QAction(QIcon('new.png'), '&New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('New Document')
        new_action.triggered.connect(self.new_file_onclick)

        exit_action = QAction(QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.file_exit_onclick)

        # Define File Menu
        file_menu.addAction(new_action)
        file_menu.addAction(exit_action)

    def dock_toolbar(self):
        toolbar = QToolBar("DoPQ-Toolbar")
        self.addToolBar(toolbar)
        img_home = QIcon('asset_files/home_glossy.png')
        img_command = QIcon('asset_files/code_command.png')

        home_btn = QAction(img_home, "Home", self)
        home_btn.setStatusTip('logo-btn')
        home_btn.triggered.connect(self.btn_onclick_func)
        toolbar.addAction(home_btn)

        toolbar.addSeparator()

        enq_btn = QAction(img_command, "Command Lists", self)
        enq_btn.setStatusTip('Sending-commands-btn')
        enq_btn.triggered.connect(self.btn_onclick_func)
        toolbar.addAction(enq_btn)
        self.setStatusBar(QStatusBar(self))

    """
    def btn_onclick_func(self, s):
        print("This button has been clicked", s)

    # Menu Bar OnClick API definitions
    def new_file_onclick(self):
        print('New')

    def file_exit_onclick(self):
        print('Exit')
    """

    def status_subwindow(self):
        """
        Summary of the function:
        ------------------------
        (a) Defining the sub-window for the priority queue status
        (b) Info would be blank for initial loading
        
        Parameters:
        -----------
        :arg: None
        :return: A dock-widget object
        """
        dock_widget = QDockWidget(self)
        # dock_widget.setTitleBarWidget(self.subdoc_custom_title_bar("status"))
        dock_widget.setTitleBarWidget(QWidget(None))
        dock_widget.setFont(self.subdoc_font_customization())
        dock_widget.setFloating(False)
        dock_widget.setFeatures(dock_widget.NoDockWidgetFeatures)
        dock_widget.setFixedWidth(self.screen_width // 2)
        dock_widget.setFixedHeight(int(self.screen_height * 2.1) // 10)  # 25% of total height
        dock_widget.setStyleSheet(css_layout.dockwidget_layout)
        dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        return dock_widget

    def running_continers_subwindow(self):
        """
        Summary of the function:
        ------------------------
        (a) Defining the sub-window for showing the running containers information

        Parameters:
        -----------
        :arg: None
        :return: A dock-widget object (sub-window)
        """
        dock_widgets = QDockWidget(self)
        # dock_widgets.setTitleBarWidget(self.subdoc_custom_title_bar("running"))
        dock_widgets.setTitleBarWidget(QWidget(None))
        dock_widgets.setFloating(False)
        dock_widgets.setFont(self.subdoc_font_customization())
        dock_widgets.setFeatures(dock_widgets.NoDockWidgetFeatures)
        dock_widgets.setFixedHeight((int(self.screen_height * 4.8) // 10))  # 48%
        dock_widgets.setFixedWidth(int(self.screen_width * 4.97) // 10)

        dock_widgets.setStyleSheet(css_layout.dockwidget_layout)
        dock_widgets.setAllowedAreas(Qt.LeftDockWidgetArea)
        return dock_widgets

    def userstats_subwindow(self):
        """
        Summary of the function:
        ------------------------
        (a) Defining the sub-window for the User Statistics

        Parameters:
        -----------
        :arg: None
        :return: A dock-widget object (sub-window)
        """
        dock_widget = QDockWidget(self)
        # dock_widget.setTitleBarWidget(self.subdoc_custom_title_bar("userstats"))
        dock_widget.setTitleBarWidget(QWidget(None))
        dock_widget.setFloating(False)
        dock_widget.setFont(self.subdoc_font_customization())
        dock_widget.setFeatures(dock_widget.NoDockWidgetFeatures)
        dock_widget.setFixedHeight((int(self.screen_height * 3.4) // 10))
        dock_widget.setFixedWidth(self.screen_width // 2)
        dock_widget.setStyleSheet(css_layout.dockwidget_layout)
        dock_widget.setAllowedAreas(Qt.TopDockWidgetArea)
        return dock_widget

    def enqueued_containers_subwindow(self):
        """
        Summary of the function:
        ------------------------
        (a) Defining the sub-window for showing the enqueued containers information

        Parameters:
        -----------
        :arg: None
        :return: A dock-widget object (sub-window)
        """
        dock_widget = QDockWidget(self)
        # dock_widget.setTitleBarWidget(self.subdoc_custom_title_bar("enqueued"))
        dock_widget.setTitleBarWidget(QWidget(None))
        dock_widget.setFloating(False)
        dock_widget.setFont(self.subdoc_font_customization())
        dock_widget.setFeatures(dock_widget.NoDockWidgetFeatures)
        dock_widget.setFixedHeight((int(self.screen_height * 4.6) // 10))  # 48%
        dock_widget.setFixedWidth(int(self.screen_width * 4.97) // 10)
        dock_widget.setStyleSheet(css_layout.dockwidget_layout)
        dock_widget.setAllowedAreas(Qt.RightDockWidgetArea)
        return dock_widget

    def history_subwindow(self):
        """
        Summary of the function:
        ------------------------
        (a) Defining the sub-window for showing executed docker containers history

        Parameters:
        -----------
        :arg: None
        :return: A dock-widget object (sub-window)
        """
        dock_widget = QDockWidget(self)
        # dock_widget.setTitleBarWidget(self.subdoc_custom_title_bar("history"))
        dock_widget.setTitleBarWidget(QWidget(None))
        dock_widget.setFloating(False)
        dock_widget.setFont(self.subdoc_font_customization())
        dock_widget.setFeatures(dock_widget.NoDockWidgetFeatures)
        dock_widget.setFixedHeight((int(self.screen_height * 3.9) // 10))
        dock_widget.setFixedWidth(self.screen_width // 2)
        dock_widget.setStyleSheet(css_layout.dockwidget_layout)
        dock_widget.setAllowedAreas(Qt.RightDockWidgetArea)
        return dock_widget
