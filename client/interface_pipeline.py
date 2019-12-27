import sys
import client.css_layout as css_layout

from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QLabel

from client.utils import log
from client.commands import shutdown_dopq
from client.view_thread import QThreadWorker
from client.parent_window import ParentWindow
from client.commands import delete_dopq_history
from client.commands import update_enqueued_list

LOG = log.get_module_log(__name__)

__authors__ = "Md Rezaur Rahman"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Reza, Ilja, Markus"
__status__ = "Dev"


def qt_main(server_obj):
    app = QtWidgets.QApplication(sys.argv)
    window_obj = InterfacePyQT(server_obj)
    window_obj.show()
    window_obj.thread_connector(server_obj)
    sys.exit(app.exec_())


class InterfacePyQT(ParentWindow):
    def __init__(self, server_obj):
        super(InterfacePyQT, self).__init__()
        self.server_obj = server_obj
        self.prev_history_containers = []
        self.prev_enqueued_containers = []
        self.prev_running_containers = []
        self.prev_user_stat = None
        self.height, self.width = self.screen_geometry_details()

        # Set boolean value for first time loading of sub-widgets
        self.is_firsttime_history_updated = True
        self.is_firsttime_userstat_updated = True
        self.is_firsttime_status_updated = True
        self.is_firsttime_curr_cont_updated = True
        self.is_firsttime_enqueued_updated = True

        # Set the update containers info from dopq_server
        self.enqueue_update_list = []
        self.history_update_list = None
        self.running_update_list = None

        # Initiate DoPQ Main Menu
        menu_list = self.dock_main_menu()
        print(menu_list)
        self.submenu_config(menu_list)

    def dock_main_menu(self):
        self.menuBar().setStyleSheet("QMenuBar::item { color: rgb(255, 255, 255); }")
        main_menu = self.menuBar()

        arena_menu = main_menu.addMenu('DoPQ-Arena')
        arena_menu.setStyleSheet("QMenu::item { color: rgb(255, 255, 255); }")

        commands_menu = main_menu.addMenu('Commands')
        commands_menu.setStyleSheet("QMenu::item { color: rgb(255, 255, 255); }")

        help_menu = main_menu.addMenu('Help')
        help_menu.setStyleSheet("QMenu::item { color: rgb(255, 255, 255); }")

        about_menu = main_menu.addMenu('About DoPQ')
        about_menu.setStyleSheet("QMenu::item { color: rgb(255, 255, 255); }")

        return [arena_menu, commands_menu, help_menu, about_menu]


    def submenu_config(self, menu_list):
        self.submenu_arena_options(menu_list[0])
        self.submenu_command_options(menu_list[1])

    def submenu_arena_options(self, arena_menu):
        """
        Summary of the function:
        ------------------------
        (a) Define the options in the 'DoPQ-Arena' Menu
        (b) Shows Containers info and user stats in details on different windows
        i.e., (i) Status Info (ii) User-Stats (iii) Running cont. (iv) Enqueued cont. (v) History

        Parameters:
        -----------
        :arg: QMenu instance
        :return: None
        """
        rc_action = QAction(QIcon('new.png'), '&Running Containers', self)
        rc_action.setShortcut('Ctrl+R')
        rc_action.setStatusTip('New Document')
        rc_action.triggered.connect(self.onclick_command_clear_history)

        enq_action = QAction(QIcon('new.png'), '&Enqueued Containers', self)
        enq_action.setShortcut('Ctrl+E')
        enq_action.setStatusTip('New Document')
        enq_action.triggered.connect(self.onclick_command_clear_history)

        dopq_stat_action = QAction(QIcon('new.png'), '&DoPQ Status', self)
        dopq_stat_action.setShortcut('Ctrl+D')
        dopq_stat_action.setStatusTip('New Document')
        dopq_stat_action.triggered.connect(self.onclick_command_clear_history)

        user_stat_action = QAction(QIcon('new.png'), '&User Statistics', self)
        user_stat_action.setShortcut('Ctrl+U')
        user_stat_action.setStatusTip('New Document')
        user_stat_action.triggered.connect(self.onclick_command_clear_history)

        history_action = QAction(QIcon('new.png'), '&History', self)
        history_action.setShortcut('Ctrl+H')
        history_action.setStatusTip('New Document')
        history_action.triggered.connect(self.onclick_command_clear_history)

        exit_action = QAction(QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.onclick_command_shutdown_dopq)

        # Define File Menu
        arena_menu.addAction(rc_action)
        arena_menu.addAction(enq_action)
        arena_menu.addAction(dopq_stat_action)
        arena_menu.addAction(user_stat_action)
        arena_menu.addAction(history_action)
        arena_menu.addAction(exit_action)

    def submenu_command_options(self, command_menu):
        """
        Summary of the function:
        ------------------------
        (a) Define the options in the 'Commands' Menu
        (b) Define set of commands initiate from client PC

        Parameters:
        -----------
        :arg: QMenu instance
        :return: None
        """

        enq_action = QAction(QIcon('new.png'), '&Update Enqueued Containers', self)
        enq_action.setShortcut('Ctrl+E')
        enq_action.setStatusTip('New Document')
        enq_action.triggered.connect(self.onclick_command_update_enqueued_list)

        clear_history_action = QAction(QIcon('new.png'), '&Clear History', self)
        clear_history_action.setShortcut('Ctrl+C')
        clear_history_action.setStatusTip('New Document')
        clear_history_action.triggered.connect(self.onclick_command_clear_history)

        exit_action = QAction(QIcon('exit.png'), '&Shutdown Queue', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.onclick_command_shutdown_dopq)

        # Define File Menu
        command_menu.addAction(enq_action)
        command_menu.addAction(clear_history_action)
        command_menu.addAction(exit_action)

    # Menu Bar OnClick API definitions
    def onclick_command_update_enqueued_list(self):
        """
        Summary of the function:
        ------------------------
        (a) Define the "Enqueued Container Update" command from the "Commands menu"
        (b) DoPQ process in the dopq_server will be locked until the update enqueued container is not finished
        (c) API for locking the DoPQ process invoked in here
        :return:
        """
        if len(self.enqueue_update_list) != 0:
            self.server_obj.dopq_system_lock(True)
            print("Call is in Update Command")
            self.floating_obj = update_enqueued_list.FloatingWindow(self.server_obj)
            self.floating_obj.create_enqueued_list(self.enqueue_update_list)

    def onclick_command_clear_history(self):
        """
            Summary of the function:
            ------------------------
            (a) Define the "Clear History" command from the "Commands menu"
            (b) Delete all previous information about docker containers build through the DoPQ system
            (c) Update the user status simultaneously
            :return:
            """
        self.diag = delete_dopq_history.ClearHistory(self.server_obj)

    def onclick_command_shutdown_dopq(self):
        self.diag = shutdown_dopq.ShutdownDoPQ(self.server_obj)

    ################################ Sub Window Updates ################################
    # -> API's for sub window update for displaying dOPQ info in Client PC             #
    # -> Data periodically updated through QThread Class                               #
    # -> All sub windows are basically dock widget objects                             #
    ####################################################################################

    ################################################
    ########## Update DOPQ System Status  ##########
    ################################################

    def dopqstat_mdi_subwin_update(self, data, isupdate):
        print("call is in dopq_status_widget_from_thread_test ")
        list_widget = QListWidget()
        if isupdate:
            html_text = css_layout.dopq_status_widget_richtext_formatting(data)
            qlistitem_obj = QListWidgetItem()
            qlabel_obj = QLabel()
            qlabel_obj.setText(html_text)
            new_font = QFont("Arial", 12, QFont.Bold)
            qlabel_obj.setFont(new_font)
            qlabel_obj.adjustSize()
            qlabel_obj.setStyleSheet(css_layout.dopq_stat_label_layout)

            qlistitem_obj.setSizeHint(qlabel_obj.sizeHint())
            list_widget.addItem(qlistitem_obj)
            list_widget.setItemWidget(qlistitem_obj, qlabel_obj)
            self.dopq_stat_dock.setWidget(list_widget)

        #self.mdi.addSubWindow(self.dopq_stat_subwin)

    ################################################
    ######### Update User Stats Sub Widget #########
    ################################################

    def userstats_mdi_subwin_update(self, data):
        print("call is in userstatus_widget_update() ")
        list_widget = QListWidget()

        if data is not None:
            for container in data:
                html_text = css_layout.user_status_widget_richtext_formatting(container)
                qlistitem_obj = QListWidgetItem()
                qlabel_obj = QLabel()
                qlabel_obj.setText(html_text)
                new_font = QFont("Arial", 16, QFont.Bold)
                qlabel_obj.setFont(new_font)
                qlabel_obj.adjustSize()
                qlabel_obj.setStyleSheet(css_layout.listwidget_label_layout)

                qlistitem_obj.setSizeHint(qlabel_obj.sizeHint())
                list_widget.addItem(qlistitem_obj)
                list_widget.setItemWidget(qlistitem_obj, qlabel_obj)

            self.prev_user_stat = data
            self.user_stats_dock.setWidget(list_widget)

    def update_userstats_window_threadcall(self, data):
        print("call is in update_userstat_threadcall()")
        if self.is_firsttime_userstat_updated:
            self.userstats_mdi_subwin_update(data)
            self.is_firsttime_userstat_updated = False

        else:
            # Check the history list is updated or not
            isupdated = False
            if self.prev_user_stat is not None:
                pairs = zip(data, self.prev_user_stat)
                if any(x != y for x, y in pairs):
                    isupdated = True
            if isupdated:
                self.userstats_mdi_subwin_update(data)

    ################################################
    ########### Update History Sub Widget ##########
    ################################################

    def history_mdi_subwin_update(self, data):
        self.history_update_list = data
        print("call is in History_widget_from_thread_test ")
        list_widget = QListWidget()
        cnt = 1

        if data is not None:
            for container in data:
                html_text = css_layout.history_containers_richtext_formatting(container, cnt)
                cnt += 1
                qlistitem_obj = QListWidgetItem()
                qlabel_obj = QLabel()
                qlabel_obj.setText(html_text)
                new_font = QFont("Arial", 16, QFont.Bold)
                qlabel_obj.setFont(new_font)
                qlabel_obj.adjustSize()
                qlabel_obj.setStyleSheet(css_layout.listwidget_label_layout)

                qlistitem_obj.setSizeHint(qlabel_obj.sizeHint())
                list_widget.addItem(qlistitem_obj)
                list_widget.setItemWidget(qlistitem_obj, qlabel_obj)

            self.prev_history_containers = data
            self.history_dock.setWidget(list_widget)

    def update_history_window_threadcall(self, data):
        print("call is in History_widget_from_thread_test :  ", data)
        if len(self.prev_history_containers) == 0:
            self.history_mdi_subwin_update(data)
        elif len(self.prev_history_containers) != len(data):
            self.prev_history_containers = []
            self.history_mdi_subwin_update(data)
        else:
            is_updated = False
            pairs = zip(data, self.prev_history_containers)
            if any(x != y for x, y in pairs):
                is_updated = True

            if is_updated:
                self.history_mdi_subwin_update(data)

    ###################################################
    ####### Update Running Container Sub Widget #######
    ###################################################

    def running_mdi_subwin_update(self, data):
        self.running_update_list = data
        print(" current_cont_widget_update : ", data)
        list_widget = QListWidget()
        cnt = 1

        if data is not None:
            print("running data is not none ... ")
            # is_first_time = False
            for container in data:
                html_text = css_layout.running_containers_richtext_formatting(container, cnt)
                cnt += 1
                qlistitem_obj = QListWidgetItem()
                qlabel_obj = QLabel()
                qlabel_obj.setText(html_text)
                new_font = QFont("Arial", 16, QFont.Bold)
                qlabel_obj.setFont(new_font)
                qlabel_obj.adjustSize()
                qlabel_obj.setStyleSheet(css_layout.listwidget_label_layout)

                qlistitem_obj.setSizeHint(qlabel_obj.sizeHint())
                list_widget.addItem(qlistitem_obj)
                list_widget.setItemWidget(qlistitem_obj, qlabel_obj)

            self.prev_running_containers = data
            self.running_containers_dock.setWidget(list_widget)

    def update_running_window_threadcall(self, data):
        print("call is in running_containers_widget_from_thread_test ")
        print("Running List: ", data)

        if len(self.prev_running_containers) == 0:
            self.running_mdi_subwin_update(data)
        elif len(self.prev_running_containers) != len(data):
            self.prev_running_containers = []
            self.running_mdi_subwin_update(data)
        else:
            is_updated = False
            pairs = zip(data, self.prev_running_containers)
            if any(x != y for x, y in pairs):
                is_updated = True

            if is_updated:
                self.running_mdi_subwin_update(data)

    #####################################################
    ######## Update Enqueued Container Sub Widget #######
    #####################################################

    def enqueued_mdi_subwin_update(self, data):
        self.enqueue_update_list = data
        print("call is in enqueued_containers update method")
        list_widget = QListWidget()
        cnt = 1

        if data is not None:
            for container in data:
                html_text = css_layout.enqueued_containers_richtext_formatting(container, cnt)
                cnt += 1
                qlistitem_obj = QListWidgetItem()
                qlabel_obj = QLabel()
                qlabel_obj.setText(html_text)
                new_font = QFont("Arial", 16, QFont.Bold)
                qlabel_obj.setFont(new_font)
                qlabel_obj.adjustSize()
                qlabel_obj.setStyleSheet(css_layout.listwidget_label_layout)

                qlistitem_obj.setSizeHint(qlabel_obj.sizeHint())
                list_widget.addItem(qlistitem_obj)
                list_widget.setItemWidget(qlistitem_obj, qlabel_obj)

            self.prev_enqueued_containers = data
            self.enqueued_dock.setWidget(list_widget)

    def update_enqueued_window_threadcall(self, data):
        print("call is in enqueued_containers_widget_from_thread_test : ", data)
        if len(self.prev_enqueued_containers) == 0:
            self.enqueued_mdi_subwin_update(data)
        elif len(self.prev_enqueued_containers) != len(data):
            self.prev_enqueued_containers = []
            self.enqueued_mdi_subwin_update(data)
        else:
            is_updated = False
            pairs = zip(data, self.prev_enqueued_containers)
            if any(x != y for x, y in pairs):
                is_updated = True

            if is_updated:
                self.enqueued_mdi_subwin_update(data)

    def thread_connector(self, dopq):
        self.thread_obj = QThreadWorker(dopq)
        LOG.info('Call is in : {}'.format("thread_connector function"))
        self.thread_obj.sig_status.connect(self.dopqstat_mdi_subwin_update)
        self.thread_obj.sig_userstat.connect(self.update_userstats_window_threadcall)
        self.thread_obj.sig_running_cont.connect(self.update_running_window_threadcall)
        self.thread_obj.sig_enqueued_cont.connect(self.update_enqueued_window_threadcall)
        self.thread_obj.sig_history.connect(self.update_history_window_threadcall)
        self.thread_obj.start()


if __name__ == "__main__":
    qt_main()
