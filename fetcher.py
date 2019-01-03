"""
small script for monitoring the amount of containers on the local drive and 
fetching new ones if needed.
This script is intended to be called from run.py with the relevant paths passed
as command line arguments.
"""

import os
import shutil
import logging
import time
import ctypes
import numpy as np
import helper_process as hp


class Fetcher(hp.HelperProcess):

    def __init__(self, config):

        super(Fetcher, self).__init__()

        self.paths = config['paths']
        self.config = config['fetcher']

        # set up logging
        self.logfile = os.path.join(self.paths['log'], "fetcher.log")
        self.logger = logging.getLogger('fetcher')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.FileHandler(self.logfile))
        # write passed directories to log
        self.logger.info(time.ctime() + "\n\tstarting fetcher process...")
        self.logger.info(
            time.ctime() + "\tpassed directories:\n\t\tlocal hard drive:\t" + self.paths['network_containers']
            + "\n\t\tshared network drive:\t" + self.paths['local_containers']
            + "\n\t\tlog-file path:\t\t" + self.paths['log'])

    def get_free_space(self, path):
        """
        helper function for examining free space on a drive
        --------------
        args:
            - path: directory that should be examined
        return: 
            - free_space_abs: absolute amount of free space in bytes
            - free_space_rel: percentage of available free space
        """

        # check if windows or unix
        if os.name == "nt":
            free_bytes, total_bytes = ctypes.c_ulonglong(0), ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, ctypes.pointer(total_bytes),
                                                       ctypes.pointer(free_bytes))
            free_space_abs = free_bytes.value
            free_space_rel = free_space_abs / total_bytes.value

        else:
            stat = os.statvfs(path)
            free_space_abs = stat.f_frsize * stat.f_bavail
            total_space = stat.f_frsize * stat.f_blocks
            free_space_rel = float(free_space_abs) / float(total_space)

        self.logger.info(
            time.ctime() + "\tFree space on hard drive: " + str(int(free_space_abs / 1024 / 1024)) + "MB which is " + \
            str(round(free_space_rel * 100, 2)) + "%")

        return free_space_abs, free_space_rel

    def move_containers(self, container_list, source_dir, target_dir):
        """
        helper function for moving containers from network share to local drive
        --------------
        args:
            - container_list: list of the container names that should be moved
            - source_dir: directory on the network share that hold the containers (source)
            - target_dir: directory on the local drive where the containers should be moved to (destination)
        """

        # write to log
        self.logger.info(time.ctime() + ":\tFetching containers form {}.".format(source_dir))
        self.logger.info("---------------------------------------------------------")

        for container in container_list:
            # move files
            shutil.move(os.path.join(source_dir, container), target_dir)

            # log containers that have been moved
            self.logger.info(time.ctime() + ":\tMoved container {} to {}".format(container, target_dir))

        # write LF to log for better readability
        self.logger.info("\n")

    def handle_invalid_containers(self):
        """
        Will detect invalid containers and create a warning in log and if flag is set, also delete the corresponding
        containers.
        :return: None
        """
        # check for invalid files and warn
        # TODO: Wrong here, should use the config to verify executors
        invalid_docker_files = [el for el in os.listdir(self.paths['network_containers'])
                                if os.path.isfile(os.path.join(self.paths['network_containers'], el))
                                and el.split('_')[-1].split('.')[0].lower() not in self.config['executors']
                                and not len(self.config['executors']) == 0]

        if len(invalid_docker_files) > 0:
            logging.warning(time.ctime() + ":\t"
                                           "The following containers are provided by persons, who are not "
                                           "authorized to run "
                                           "containers on this machine:\n {}".format(invalid_docker_files))

            if self.config['remove_invalid']:
                for filename in invalid_docker_files:
                    file_path = os.path.join(self.paths['network_containers'], filename)
                    os.remove(file_path)
            else:
                invalid_path = os.path.join(self.paths['network_containers'], 'invalid') + '/'
                if not os.path.exists(invalid_path): os.makedirs(invalid_path)
                for filename in invalid_docker_files:
                    file_path = os.path.join(self.paths['network_containers'], filename)
                    shutil.move(file_path, invalid_path)

    def fetch(self):

        source_dir = self.paths['network_containers']
        target_dir = self.paths['local_containers']

        # control variable for while loop
        first_run = True

        # start monitoring loop
        while 1:

            # wait from the second iteration onward before fetching containers
            if not first_run:
                time.sleep(self.config['sleep'])
            else:
                first_run = not first_run

            # check if enough space is present on hard drive
            free_space_abs, free_space_rel = self.get_free_space(target_dir)
            if free_space_rel < self.config['min_space']:
                self.logger.info(time.ctime() + "\tnot enough space to fetch new containers")
                continue

            # check if invalid containers are present
            self.handle_invalid_containers()

            # get list of containers on network drive
            container_list = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]

            # check if any containers are on the network drive
            if len(container_list) == 0:
                self.logger.info(time.ctime() + "\tno containers to fetch")
                continue

            # get filesizes of the network containers
            container_list_sizes = [os.stat(os.path.join(source_dir, container)).st_size
                                    for container in container_list]

            # check if there is enough space to move all files
            if np.sum(container_list_sizes) < free_space_abs:
                # move containers
                self.move_containers(container_list, source_dir, target_dir)
                continue

            # remove files until they fit on the hard drive
            self.logger.info(time.ctime() + "\tnot enough space to fetch all containers...fetching only a part of them")

            # clone lists for modification
            tmp_container_list = container_list
            tmp_container_list_sizes = container_list_sizes

            # iteratively remove containers
            while np.sum(tmp_container_list_sizes) > free_space_abs:
                tmp_container_list.pop()
                tmp_container_list_sizes.pop()
                if len(tmp_container_list) == 1:
                    if tmp_container_list_sizes[0] > free_space_abs:
                        continue
                    else:
                        break

            # move containers
            self.move_containers(container_list, source_dir, target_dir)
            continue

    def start(self):

        super(Fetcher, self).start(self.fetch)
        return self.process.pid


if __name__ == "__main__":

    import argparse
    import configparser


    def parse_config(configfile):
        # create config parser and read file
        config = configparser.ConfigParser()
        config.read(configfile)

        # parse settings into dicts
        parsed_config = {
            'paths': {'local_containers': config.get('paths', 'container.dir'),
                      'network_containers': config.get('paths', 'network.dir'),
                      'build': config.get('paths', 'build.dir'),
                      'load': config.get('paths', 'load.dir'),
                      'log': config.get('paths', 'log.dir')},

            'docker': {'mounts': config.get('docker', 'mount.volumes').split(','),
                       'run': config.get('docker', 'run.params').split(','),
                       'mem': config.get('docker', 'mem.limit'),
                       'max_gpus': config.getint('docker', 'max.assignment')},

            'queue': {'max_history': config.getint('queue', 'max.history'),
                      'verbose': config.getboolean('queue', 'verbose'),
                      'sleep': config.getint('queue', 'sleep.interval')},

            'builder': {'sleep': config.getint('builder', 'sleep.interval'),
                        'load': config.get('builder', 'load.suffix').split(','),
                        'build': config.get('builder', 'build.suffix').split(',')},

            'fetcher': {'remove_invalid': config.getboolean('fetcher', 'remove.invalid.containers'),
                        'sleep': config.getint('fetcher', 'sleep.interval'),
                        'min_space': config.getfloat('fetcher', 'min.space'),
                        'executors': config.get('fetcher', 'valid.executors').split(',')}}

        return parsed_config


    parser = argparse.ArgumentParser(description='process for fetching docker containers from network to local storage')
    parser.add_argument(parser.add_argument('-c', '--config', type=str, dest='configfile', metavar='filename',
                                            default='config.ini'))

    args = vars(parser.parse_args())

    fetcher = Fetcher(**args)
    try:
        fetcher.start()
    finally:
        fetcher.stop()
