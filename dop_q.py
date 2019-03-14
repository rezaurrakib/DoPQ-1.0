#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
======================================================
***         Docker Priority Queue (DoP-Q)          ***
======================================================

    |Purpose: Priority queue to run docker containers

Created on Mon May 29 23:21:42 2017

History:
    16.10.2017: Changed to python 2.7
    14.03.2019: Code refactoring initiated	

@author: markus
"""


import configparser
import datetime
import os
import threading
import time
import traceback

import dill
import docker
import numpy as np
from docker.errors import APIError
from pathos.helpers import mp


import helper_process as hp
import provider
from utils import interface
from utils import log
from utils.gpu import GPU, get_gpus_status


class DopQ(hp.HelperProcess):

    def __init__(self, configfile='config.ini', logfile='dopq.log', debug=False):

        # init logging
        self.logger = log.init_log(logfile)

        # get settings from config
        if not os.path.isfile(configfile):
            self.write_default_config(configfile)

        # init member variables
        self.starttime = None
        self.client = docker.from_env()
        self.debug = debug
        self.configfile = configfile
        self.logfile = logfile
        self.config = self.parse_config(configfile)
        self.paths = self.config['paths']
        self.history_file = 'history.dill'
        self.container_list_file = 'container_list.dill'
        self.running_containers_file = 'running_containers.dill'
        self.container_list = []
        self.running_containers = []
        self.history = []
        self.mapping = self.restore('all')

        # init helper processes and classes
        self.queue = mp.Queue()
        self.provider = provider.Provider(self.config, self.queue)

        # build all non-existent directories, except the network container share
        keys = list(self.paths.keys())
        for key in keys:
            if key != 'network_containers':
                if not os.path.isdir(self.paths[key]):
                    os.makedirs(self.paths[key])

        # initialize process variable and termination flag
        super(DopQ, self).__init__()

        # initialize interface as a thread (so that members of the queue are accessible by the interface)
        self.thread = threading.Thread(target=self.run_queue)

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
        if self.starttime is None:
            return '0s'

        diff = time.time() - self.starttime

        # break down diff into seconds, minutes, hours and days
        diff, seconds = divmod(int(diff), 60)
        diff, minutes = divmod(diff, 60)
        days, hours = divmod(diff, 24)

        # convert information to print format
        uptime = ''
        uptime += '{}d '.format(days) if days else ''
        uptime += '{}h '.format(hours) if hours else ''
        uptime += '{}m '.format(minutes) if minutes else ''
        uptime += '{}s'.format(seconds) if not minutes else ''

        starttime = datetime.datetime.fromtimestamp(self.starttime).strftime("%a, %d.%b %H:%M")

        return uptime, starttime

    @property
    def status(self):

        if self.starttime is None:
            return 'not started'
        elif self.thread.isAlive():
            return 'running'
        else:
            return 'terminated'

    @property
    def user_list(self):
        return self.config['fetcher']['executors']

    @property
    def users_stats(self):
        users = self.config['fetcher']['executors']
        user_stats = []

        # get info for all users
        for user in users:

            single_user_stats = {'user': user,
                                 'penalty': round(self.calc_penalty(user), 4),
                                 'containers run': self.find_user_in_containers(user, self.history),
                                 'containers enqueued': self.find_user_in_containers(user, self.container_list)}

            user_stats.append(single_user_stats)

        return user_stats

    @staticmethod
    def find_user_in_containers(user, container_list):
        """
        small helper for counting how many containers in the list belong to user
        :param user: name of the user
        :param container_list: list with Container objects
        :return: number of user's containers in container_list
        """

        num_containers = 0
        for container in container_list:
            if container.user == user:
                num_containers += 1

        return num_containers

    def restore(self, key):
        """
        restores history, container_list, running_containers, or all three
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
                    assignment_tuple[1] = dill.load(f)
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
        saves history, container_list, running_containers, or all three
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

    def update_container_list(self):
        update_list = []

        # add new images that are obtained from the builder process
        while not self.queue.empty():
            update_list.append(self.queue.get())
        self.container_list += update_list

        # sort priority queue:
        self.container_list = sorted(self.container_list, key=self.sort_fn)

    def update_running_containers(self):
        for container in self.running_containers:
            if container.status == 'exited':
                container.stop_stats_stream()
                self.history.insert(0, container)
                self.running_containers.remove(container)

    def get_user_oh(self, user_name):
        user_oh = [int(self.get_user(el) == user_name.lower()) for el in self.history]
        return np.array(user_oh)

    def calc_exp_decay(self):
        decay = [np.exp(-i) for i in range(len(self.history))]
        return np.array(decay)

    def calc_penalty(self, user_name):
        user_oh = self.get_user_oh(user_name)
        return np.sum(user_oh * self.calc_exp_decay())

    def get_user(self, container):
        return container.user

    def split_and_calc_penalty(self, container):
        user = self.get_user(container)
        return self.calc_penalty(user)

    def sort_fn(self, container):
        """
        function that is used for sorting the container list
        :param container: container object from the list
        :return: tuple consisting of user penalty and creation time of the container
        """
        return self.split_and_calc_penalty(container), container.created_at

    def show_penalties(self, docker_users):
        for user in docker_users:
            print("Penalty for {}: {}".format(user, round(self.calc_penalty(user), 4)))

    def sleep(self):
        time.sleep(self.config['queue']['sleep'])

    @staticmethod
    def write_default_config(configfile):
        """
        Write default configuration
        :return: None
        """

        config = configparser.ConfigParser()

        config.add_section('paths')

        config.set('paths', 'container.dir', '/home/rrahman/Desktop/LMU_AUGEN_REPO/DOPQ_Config_Folders/container')
        config.set('paths', 'network.dir', '/home/rrahman/Desktop/LMU_AUGEN_REPO/DOPQ_Config_Folders/network')
        config.set('paths', 'unzip.dir', '/home/rrahman/Desktop/LMU_AUGEN_REPO/DOPQ_Config_Folders/unzip')
        config.set('paths', 'log.dir', '/home/rrahman/Desktop/LMU_AUGEN_REPO/DOPQ_Config_Folders/log')
        config.set('paths', 'history.dir', '/home/rrahman/Desktop/LMU_AUGEN_REPO/DOPQ_Config_Folders/history')
        config.set('paths', 'failed.dir', '/home/rrahman/Desktop/LMU_AUGEN_REPO/DOPQ_Config_Folders/failed')

        config.add_section('queue')
        config.set('queue', 'max.history', '100')
        config.set('queue', 'verbose', 'yes')
        config.set('queue', 'sleep.interval', '60')
        config.set('queue', 'max.gpu.assignment', '1')

        config.add_section('docker')
        config.set('docker', 'mount.volumes', '/media/data/expImages:/imgdir,/media/local/output_container:/outdir')
        config.set('docker', 'remove', 'yes')
        config.set('docker', 'network.mode', 'host')
        config.set('docker', 'mem.limit', '32g')
        config.set('docker', 'logging.interval', '10')

        config.add_section('fetcher')
        config.set('fetcher', 'valid.executors', 'reza,anees,ilja,markus,reza')
        config.set('fetcher', 'min.space', '0.05')
        config.set('fetcher', 'remove.invalid.containers', 'yes')
        config.set('fetcher', 'sleep.interval', '60')

        config.add_section('builder')
        config.set('builder', 'sleep.interval', '60')
        config.set('builder', 'load.suffix', 'tar')
        config.set('builder', 'build.suffix', 'zip')

        # store config
        with open(configfile, 'w') as conf:
            config.write(conf)

    @staticmethod
    def parse_config(configfile):

        # create config parser and read file
        config = configparser.ConfigParser()
        config.read(configfile)

        # parse settings into dicts
        parsed_config = {
            'paths': {'local_containers': config.get('paths', 'container.dir'),
                      'network_containers': config.get('paths', 'network.dir'),
                      'unzip': config.get('paths', 'unzip.dir'),
                      'log': config.get('paths', 'log.dir'),
                      'history': config.get('paths', 'history.dir'),
                      'failed': config.get('paths', 'failed.dir')},

            'docker': {'mounts': config.get('docker', 'mount.volumes').split(','),
                       'auto_remove': config.getboolean('docker', 'remove'),
                       'mem_limit': config.get('docker', 'mem.limit'),
                       'network_mode': config.get('docker', 'network.mode'),
                       'logging_interval': config.getint('docker', 'logging.interval')},

            'queue': {'max_history': config.getint('queue', 'max.history'),
                      'verbose': config.getboolean('queue', 'verbose'),
                      'sleep': config.getint('queue', 'sleep.interval'),
                      'max_gpus': config.getint('queue', 'max.gpu.assignment')},

            'builder': {'sleep': config.getint('builder', 'sleep.interval'),
                        'load': config.get('builder', 'load.suffix').split(','),
                        'build': config.get('builder', 'build.suffix').split(',')},

            'fetcher': {'remove_invalid': config.getboolean('fetcher', 'remove.invalid.containers'),
                        'sleep': config.getint('fetcher', 'sleep.interval'),
                        'min_space': config.getfloat('fetcher', 'min.space'),
                        'executors': config.get('fetcher', 'valid.executors').split(',')}}

        return parsed_config

    def reload_config(self, report_fn=None):

        # init report fn if not given
        if report_fn is None:
            report_fn = self.logger

        report_fn('reloading config: {:.1f} %'.format(0))
        self.config = self.parse_config(self.configfile)

        # loading done
        report_fn('reloading config: {:.1f} %'.format(50))

        # set new config
        self.paths = self.config['paths']
        self.provider.paths = self.config['paths']
        self.provider.fetcher_conf = self.config['fetcher']
        self.provider.builder_conf = self.config['builder']
        self.provider.docker_conf = self.config['docker']

        # loading done
        report_fn('reloading config: {:.1f} %'.format(100))

    def stop(self):
        self.term_flag.value = 1
        GPU.stop_hardware_monitor()
        self.provider.stop()
        if self.status == 'running':
            self.thread.join()

    def start(self):

        try:
            self.starttime = time.time()
            #self.run_queue()
            self.thread.start()
            self.provider.start()
            interface.run_interface(self)
        finally:
            self.stop()

    def run_queue(self):
        """
        Runs the priority queue.

        :return: None
        """

        try:
            # run this until forced to quit
            while True:

                # exit queue process if termination flag is set
                if self.term_flag.value:
                    raise RuntimeError('\tqueue is shutting down')

                # update container list
                self.update_container_list()

                # clean up running containers
                self.update_running_containers()

                # check if there are containers in the queue
                if len(self.container_list) == 0:
                    self.sleep()
                    continue

                # TODO implement slot system

                # get next container
                container = self.container_list.pop(0)
                gpu = container.use_gpu

                # keep cycling if container requires gpu but none are available
                # Added by reza ... Use API from gpu instead of gpu_handler
                free_minors = get_gpus_status()
                if len(free_minors) == 0 and gpu:
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
            self.save('all')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="priority queue for running docker containers")
    parser.add_argument('-l', '--logfile', type=str, dest='logfile', metavar='filename', default='dopq.log')
    parser.add_argument('-c', '--config', type=str, dest='configfile', metavar='filename', default='config.ini')
    parser.add_argument('--debug', action='store_true')

    args = vars(parser.parse_args())

    dop_q = DopQ(**args)
    dop_q.start()
