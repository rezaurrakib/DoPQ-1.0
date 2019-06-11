import copy
from collections import OrderedDict
from pyqt_interface.base_window_controller import DisplayFunction
from PyQt5.QtCore import pyqtSignal, QThread

from math import floor, ceil

from utils import log

LOG = log.get_module_log(__name__)


class QThreadWorker(QThread):
    sig1 = pyqtSignal(dict, bool)
    sig2 = pyqtSignal(list)
    sig3 = pyqtSignal(list)

    def __init__(self, dopq, parent=None):
        QThread.__init__(self, parent)
        self.dopq = dopq
        self.status_display_info = []
        self.running_cont_display_info = []


    def fetch_history_info(self):
        information = self.dopq.history


        pass


    def fetch_running_containers_info(self):
        information = []
        containers = copy.copy(self.dopq.running_containers)
        print("Number of Running containers: ", len(containers))
        for container in self.dopq.running_containers:
            print("container: ", container.container_stats())
            information.append(container.container_stats())

            # reformat gpu info
            gpu_info = information[-1].pop('gpu', False)
            if gpu_info:
                minors, usages = [], []
                for info in gpu_info:
                    minors.append(info['id'])
                    usages.append(info['usage'])
                information[-1]['id'] = minors
                information[-1]['usage'] = ''.join([str(usage) + '% ' for usage in usages])

        return information


    def fetch_enqueued_containers_info(self):
        container_list = self.dopq.container_list
        information = [container.history_info() for container in container_list]
        print("Enqueued Information: ", information)
        return information

    def fetch_status_info(self):
        information = {}
        info_update = True
        information['Queue Status'] = self.dopq.status

        if information['Queue Status'] == 'running':
            information['Queue Uptime'], information['Queue Starttime'] = self.dopq.uptime
            information["Provider Status"] = self.dopq.provider.status
            if information['Provider Status'] == 'running':
                information['Provider Uptime'], information['Provider Starttime'] = self.dopq.provider.uptime
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
            self.sig1.emit(status_info, isupdate)
            self.sig2.emit(running_cont_info)
            self.sig3.emit(enqueued_cont_info)
            self.sleep(3)

""" 
    Display class for DopQ Status information
"""
'''
class Status(DisplayFunction):
    def __init__(self, subwindow, dopq):
        super(Status, self).__init__(subwindow, dopq)

        # init fields
        self.fields = {'queue status': '',
                       'queue uptime': '',
                       'queue starttime': '',
                       'provider status': '',
                       'provider uptime': '',
                       'provider starttime': ''}

        # init information dict
        self.displayed_information = copy.deepcopy(self.fields)

        self.template = [['queue: '], ['uptime:  '], ['starttime: '],
                           ["\n"],
                           ['provider: '], ['uptime:  '], ['starttime:  '],
                           ['\n']
                        ]


    def update_info(self):

        LOG.info('Command is in: {}'.format("Status call() is in update_info"))

        # gather new information
        information = {}
        information['queue status'] = self.dopq.status

        if information['queue status'] == 'running':
            information['queue uptime'], information['queue starttime'] = self.dopq.uptime
            information['provider status'] = self.dopq.provider.status

            if information['provider status'] == 'running':
                information['provider uptime'], information['provider starttime'] = self.dopq.provider.uptime
            else:
                information['provider uptime'], information['provider starttime'] = '', ''

        else:
            information['queue uptime'], information['queue starttime'] = '', ''
            information['provider status'] = ''
            information['provider uptime'], information['provider starttime'] = '', ''


        # update displayed information
        for field, value in list(information.items()):
            print("field,value :", field, value)

            # skip if information has not changed
            if value == self.displayed_information[field]:
                continue

            # overwrite information that has changed
            #attrs = pick_color(value) | self.screen.BOLD if 'status' in field else 0
            #self.update_dock_content(value, self.fields[field])

        self.displayed_information = information

    def load_template(self):
        """
        writes template to display on first call
        :return:
        """
        LOG.info('Command is in: {}'.format("Status call() is in load_template"))
        # get the beginning and end coordinates for every string in the template
        #coordinates = self.screen.addmultiline(self.template)
        fields = {'queue status': "Not Running",
                  'queue uptime': "Nil",
                  'queue starttime': "Nil",
                  'provider status': "Not Running",
                  'provider uptime': "Nil",
                  'provider starttime': "Nil"
                  }

        # sort the dict according to y coordinates first and x coordinates second
        def sort_fn(item):
            return item[1]['beginning']['y'], item[1]['beginning']['x']

        #fields = OrderedDict(sorted(list(fields.items()), key=sort_fn))
        #self.fields = self.calculate_field_properties(fields)

        self.first_call = False


class RunningContainers(DisplayFunction):
    def __init__(self, subwindow, dopq):
        super(RunningContainers, self).__init__(subwindow, dopq)
        pass


class EnqueuedContainers(DisplayFunction):
    def __init__(self, subwindow, dopq):
        super(EnqueuedContainers, self).__init__(subwindow, dopq)
        pass


class UserStats(DisplayFunction):
    def __init__(self, subwindow, dopq):
        super(UserStats, self).__init__(subwindow, dopq)
        pass


class History(DisplayFunction):
    def __init__(self, subwindow, dopq):
        super(History, self).__init__(subwindow, dopq)
        pass

'''