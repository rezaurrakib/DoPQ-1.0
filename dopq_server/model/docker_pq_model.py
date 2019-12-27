import os
import dill
import time
import datetime
import traceback
import threading
import multiprocessing as mp

from dopq_server.model.utils import log
from docker.errors import APIError
from dopq_server.model.utils.gpu import get_gpus_status
from dopq_server.model.model_helper import ModelHelper


__authors__ = "Ilja Mankov, Markus Rohm, Md Rezaur Rahman"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Reza, Ilja, Markus"
__status__ = "Dev"


class DopQContainer():
    """
    Parent class for running the priority queue of containers
    """
    def __init__(self, configfile='config.ini', logfile='dopq.log'):
        self.starttime = None
        self.helper_obj = ModelHelper()
        self.terminating_flag = False
        self.history_file = 'history.dill'
        self.container_list_file = 'container_list.dill'
        self.running_containers_file = 'running_containers.dill'
        self.history = []
        self.container_list = []
        self.running_containers = []
        self.lock_state = False
        # Variables that are initialized only once in a lifetime
        # writing configuration details into configfile
        if not os.path.isfile(configfile):
            self.helper_obj.write_default_config(configfile)
        self.config = self.helper_obj.parse_config(configfile) # Get the config dictionary
        self.paths = self.config['paths']
        self.dopq_process = None
        self.queue = mp.Queue()

        self.mapping = self.restore('all')
        self.logger = log.init_log(logfile)
        self.helper_obj.set_dopq_history(self.history)

    def start_dopq_process(self):
        """
        Register the container queue as a process.
        :return: dopq_process id
        """
        self.process_starttime()
        self.dopq_process = threading.Thread(target=self.exec_dopq_process)
        self.dopq_process.start()

    @property
    def mapping(self):
        return {
            'history': [self.history_file, self.history],
            'list': [self.container_list_file, self.container_list],
            'running': [self.running_containers_file, self.running_containers]
        }

    @mapping.setter
    def mapping(self, value):
        self.history_file, self.history = value['history']
        self.container_list_file, self.container_list = value['list']
        self.running_containers_file, self.running_containers = value['running']

    @property
    def uptime(self):
        days = 0
        elapsed_time = time.time() - self.starttime
        elapsed_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        hours, minutes, seconds = map(int, elapsed_time.split(':'))
        #print("Hours: ", hours, " Minutes : ", minutes, " Seconds: ", seconds)
        if hours >= 24:
            days = hours / 24

        # convert information to print format
        uptime = ''
        uptime += '{}d '.format(days) if days else ''
        uptime += '{}h '.format(hours) if hours else ''
        uptime += '{}m '.format(minutes) if minutes else ''
        uptime += '{}s '.format(seconds) if seconds else ''

        return uptime, self.startime_formatted

    @property
    def status(self):
        if self.dopq_process.isAlive():
            return 'running'
        elif self.starttime is None:
            return 'not started'
        else:
            return 'terminated'

    @property
    def user_list(self):
        return self.config['fetcher']['executors']

    @property
    def users_stats(self):
        users = self.config['fetcher']['executors']
        user_stats = [] # Each entry is a userstat in dict form

        # get info for all users
        for user in users:
            single_user_stats = {'user': user,
                                 'penalty': round(self.helper_obj.calc_penalty(user), 4),
                                 'containers run': self.helper_obj.container_freq_for_user(user, self.history),
                                 'containers enqueued': self.helper_obj.container_freq_for_user(user, self.container_list)}

            user_stats.append(single_user_stats)

        return user_stats

    def process_starttime(self):
        self.starttime = time.time()
        self.startime_formatted = datetime.datetime.fromtimestamp(self.starttime).strftime("%A, %d.%b %H:%M:%S")
        print("Current time: ", self.startime_formatted)

    def sleep(self):
        time.sleep(self.config['queue']['sleep'])

    def lock_update(self, is_lock):
        """
        Summary of the function:
        ------------------------
        (a) locking the DoPQ for updating the Enqueued container list from client side

        :param is_lock: boolean for acquire / release the lock state
        :return: None
        """
        if is_lock:
            self.lock_state = True
        else:
            self.lock_state = False

    def restore(self, key):
        """
        Summary of the function:
        ------------------------
        (a) Restores history, container_list, running_containers, or all three

        Parameters:
        -----------
        :param key: dictionary key of self.mapping or 'all'
        :return: None
        """

        def restore_single(path, assignment_tuple):
            """
            helper for loading a single queue list
            :param path: directory of the dill file
            :param assignment_tuple: tuple of (name of the dill file, member that will be assigned the list)
            :return: None
            """
            file_name = assignment_tuple[0]
            full_path = os.path.join(path, file_name)
            if os.path.isfile(full_path):
                with open(full_path, 'rb') as f:
                    assignment_tuple[1] = dill.load(f) # load the container queue as list
            else:
                assignment_tuple[1] = []

        mapping_dict = self.mapping
        if key == 'all':
            for item in list(mapping_dict.values()):
                restore_single(self.paths['history'], item)
        else:
            restore_single(self.paths['history'], mapping_dict[key])
            if key == 'running':
                self.update_running_containers()
        return mapping_dict

    def save(self, key):
        """
        Summary of the function:
        ------------------------
        (a) Saves history, container_list, running_containers, or all three

        Parameters:
        -----------
        :param key: dictionary key of self.mapping or 'all'
        :return: None
        """

        def save_single(path, assignment_tuple):
            """
            helper for saving a single queue list
            :param path: directory of the dill file
            :param assignment_tuple: tuple of (name of the dill file, member that will be assigned the list)
            :return: None
            """
            file_name, member = assignment_tuple
            full_path = os.path.join(path, file_name)
            for container in member:
                container.stop_stats_stream()
            with open(full_path, 'wb') as f:
                dill.dump(member, f)

        if key == 'all':
            for item in list(self.mapping.values()):
                save_single(self.paths['history'], item)
        else:
            if key == 'running':
                self.update_running_containers()
            elif key == 'list':
                self.update_container_list()
            save_single(self.paths['history'], self.mapping[key])

    #################################### APIs ####################################
    # Series of APIs containing Docker Containers information in different states
    # Should not be directly accessible from viewcontroller
    # Only be accessible from the DataPlatform class
    #############################################################################

    def update_running_containers(self):
        """
        Summary of the function:
        ------------------------
        (a) Remove specific container from the running container.
        (b) list the containers which have been done executing, i.e., status : 'exited'
        (c) Insert that container at the top of the history list (Latest executed container)

        Parameters:
        -----------
        :arg: None
        :return: None
        """
        print("Call is in update_running_containers(), curr. length: ", len(self.running_containers))
        for container in self.running_containers:
            if container.status == 'exited':
                container.stop_stats_stream()
                self.history.insert(0, container)
                self.running_containers.remove(container)

        print("(dopq) Current history_list length: ", len(self.history))
        print("(dopq) Current History: ")
        for c in self.history:
            print(c.history_info())
        print("Current running_list length: ", len(self.running_containers))

    def update_container_list(self):
        """
        Summary of the function:
        ------------------------
        (a) Update the container list by adding new images obtained from the provider process
        (b) sort the updated container list according to the penalty calculation.

        Parameters:
        -----------
        :arg: None
        :return: None
        """
        update_list = []
        print("Queue Size Now : ", self.queue.qsize())
        while not self.queue.empty():
            update_list.append(self.queue.get())
        self.container_list += update_list

        self.container_list = sorted(self.container_list, key=self.helper_obj.sort_fn)
        print("(dopq) Current Container List: ")
        for container in self.container_list:
            print(container.history_info())

    def cont_update_after_deletion(self, del_list):
        """
        Summary of the Function:
        ------------------------
        (a) Update/delete unwanted containers from the Enqueued List (i.e., self.container_list)
        (b) Command initiated from the client PC

        Parameters:
        -----------
        :arg: del_list is a list of dictionaries
        :return: None
        """
        for cont_dict in del_list:
            print("Should Deleted this Cont.: ", cont_dict)
            for container in self.container_list:
                temp = container.history_info()
                if cont_dict["name"] == temp["name"]:
                    self.container_list.remove(container)

        print("container_list Length (after deletion): ", len(self.container_list))
        print("container_list (after deletion): ")

        for c in self.container_list:
            print(c.history_info())

    ################################## Execute Priority Queue #################################
    # This private API is launched in a separate process.
    # Runs parallelly with the provider process
    # Infinitely Checks for a new docker container from the provider process
    ###########################################################################################

    def exec_dopq_process(self):
        """
        Summary of the function:
        ------------------------
        (a) Method for running the priority queue infinitely
        (b) Update the container list and running container list
        (c) Runs in a separate multiprocess

        Parameters:
        -----------
        :arg: None
        :return: None
        """
        try:
            while True:
                # exit queue process if termination flag is set
                if self.terminating_flag:
                    raise RuntimeError('\tDoPQ is shutting down')

                if self.lock_state:
                    print("DoPQ is in lock state (infinity loop)")
                    time.sleep(1)
                    continue
                else:
                    print("DoPQ is running without interruption")
                    self.update_container_list()
                    self.update_running_containers() # For cleaning up running containers
                    if len(self.container_list) == 0:
                        self.sleep()
                        continue

                    container = self.container_list.pop(0) # get next container
                    gpu = container.use_gpu

                    for c in self.container_list:
                        print(c.history_info())

                    gpu = container.use_gpu
                    free_minors = get_gpus_status()
                    if len(free_minors) == 0 and gpu: # keep cycling if container requires gpu but none are available
                        self.container_list.insert(0, container)
                        self.sleep()
                        continue

                    # start the container, write to log and append it to running containers
                    try:
                        container.start()

                    except IOError as e:
                        # put container back in the queue if not enough gpus are available
                        self.container_list.insert(0, container)
                        continue

                    except APIError:
                        continue

                    else:
                        # add to running containers and write log message
                        self.running_containers.append(container)
                        self.logger.info('\tsuccessfully ran a container from {}'.format(container))
                        self.sleep()

        except Exception as e:
            self.logger.error(traceback.format_exc())

        finally:
            # save history, container list and running containers whenever the loop is exited for whatever reason
            print("DoPQ thread is about to stop ... saving all data")
            self.save('all')

    def dopq_stop(self):
        if self.status == 'running':
            print("Terminating the thread")
            self.dopq_process.join()
