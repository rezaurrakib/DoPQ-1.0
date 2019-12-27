from client.utils import log
from PyQt5.QtCore import pyqtSignal, QThread

LOG = log.get_module_log(__name__)

__authors__ = "Md Rezaur Rahman"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Reza, Ilja, Markus"
__status__ = "Dev"


class QThreadWorker(QThread):
    sig_status = pyqtSignal(dict, bool)
    sig_running_cont = pyqtSignal(list)
    sig_enqueued_cont = pyqtSignal(list)
    sig_history = pyqtSignal(list)
    sig_userstat = pyqtSignal(list)

    def __init__(self, server_obj, parent=None):
        QThread.__init__(self, parent)
        self.dopq_server_obj = server_obj
        self.status_display_info = []
        self.running_cont_display_info = []

    def fetch_history_info(self):
        information = self.dopq_server_obj.get_containers_history_info
        return information

    def fetch_user_stats(self):
        information = self.dopq_server_obj.get_dopq_user_statistics
        return information

    def fetch_running_containers_info(self):
        information = self.dopq_server_obj.get_running_containers_info
        return information

    def fetch_enqueued_containers_info(self):
        information = self.dopq_server_obj.get_enqueued_containers_info
        return information

    def fetch_status_info(self):
        information = {}
        info_update = True
        system_update_info = self.dopq_server_obj.get_dopq_system_status
        information['Queue Status'] = system_update_info[0]

        if information['Queue Status'] == 'running':
            information['Queue Uptime'], information['Queue Starttime'] = system_update_info[1]
            information["Provider Status"] = system_update_info[2]
            if information['Provider Status'] == 'running':
                information['Provider Uptime'], information['Provider Starttime'] = system_update_info[3]
            else:
                information['Provider Uptime'], information['Provider Starttime'] = '', ''

        else:
            information['Queue Uptime'], information['Queue Starttime'] = '', ''
            information['Provider Status'] = ''
            information['Provider Uptime'], information['Provider Starttime'] = '', ''

        return information, info_update

    def run(self):
        self.running = True
        while self.running:
            status_info, isupdate = self.fetch_status_info()
            running_cont_info = self.fetch_running_containers_info()
            enqueued_cont_info = self.fetch_enqueued_containers_info()
            user_stat = self.fetch_user_stats()
            dopq_history = self.fetch_history_info()

            self.sig_status.emit(status_info, isupdate)
            self.sig_running_cont.emit(running_cont_info)
            self.sig_enqueued_cont.emit(enqueued_cont_info)
            self.sig_userstat.emit(user_stat)
            self.sig_history.emit(dopq_history)
            self.sleep(1)