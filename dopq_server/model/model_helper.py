import os
import pickledb
import configparser
import numpy as np


class ModelHelper():
    def __init__(self):
        self.dopq_history = None

    def build_directories(self, paths):
        """
        # build all non-existent directories, except the network container share
        :param paths:
        :return: None
        """
        keys = list(paths.keys())
        for key in keys:
            if key != 'network_containers':
                if not os.path.isdir(paths[key]):
                    os.makedirs(paths[key])

    @staticmethod
    def get_users_db():
        user_db_path = "/home/reza/Desktop/lmu_augenKlinikRepo/dopq_user_database/dopq_database.db" # Put user database path in here
        userlist_str = ""
        db = pickledb.load(user_db_path, False)
        userlist = db.getall()
        for k in userlist:
            userlist_str += k + ","
        userlist_str = userlist_str[:-1]
        print(userlist_str)
        return userlist_str

    @staticmethod
    def write_default_config(configfile):
        """
        Write default configuration
        :return: None
        """

        config = configparser.ConfigParser()

        config.add_section('paths')

        config.set('paths', 'container.dir', '/home/reza/Desktop/lmu_augenKlinikRepo/dopq_config_folders/container')
        config.set('paths', 'network.dir', '/home/reza/Desktop/lmu_augenKlinikRepo/dopq_config_folders/network')
        config.set('paths', 'unzip.dir', '/home/reza/Desktop/lmu_augenKlinikRepo/dopq_config_folders/unzip')
        config.set('paths', 'log.dir', '/home/reza/Desktop/lmu_augenKlinikRepo/dopq_config_folders/log')
        config.set('paths', 'history.dir', '/home/reza/Desktop/lmu_augenKlinikRepo/dopq_config_folders/history')
        config.set('paths', 'failed.dir', '/home/reza/Desktop/lmu_augenKlinikRepo/dopq_config_folders/failed')
        config.set('paths', 'user_database.dir', '/home/reza/Desktop/lmu_augenKlinikRepo/dopq_user_database/dopq_database.db')

        config.add_section('queue')
        config.set('queue', 'max.history', '500')
        config.set('queue', 'verbose', 'yes')
        config.set('queue', 'sleep.interval', '10')
        config.set('queue', 'max.gpu.assignment', '1')

        config.add_section('docker')
        config.set('docker', 'mount.volumes',
                   '/home/reza/Desktop/lmu_augenKlinikRepo/dopq_mount_folder:/imgdir,/home/reza/Desktop/lmu_augenKlinikRepo/dopq_mount_folder:/outdir')
        config.set('docker', 'remove', 'yes')
        config.set('docker', 'network.mode', 'host')
        config.set('docker', 'mem.limit', '32g')
        config.set('docker', 'logging.interval', '10')

        config.add_section('fetcher')
        #config.set('fetcher', 'valid.executors', 'reza,anees,ilja,markus,kubilay')
        config.set('fetcher', 'valid.executors', ModelHelper.get_users_db())
        config.set('fetcher', 'min.space', '0.05')
        config.set('fetcher', 'remove.invalid.containers', 'yes')
        config.set('fetcher', 'sleep.interval', '10')

        config.add_section('builder')
        config.set('builder', 'sleep.interval', '10')
        config.set('builder', 'load.suffix', 'tar')
        config.set('builder', 'build.suffix', 'zip')

        # store config
        with open(configfile, 'w') as conf:
            config.write(conf)

    @staticmethod
    def parse_config(configfile):
        """
        create config parser and read file
        :param configfile:
        :return: parse settings into dicts and returns it
        """
        config = configparser.ConfigParser()
        config.read(configfile)

        parsed_config = {
            'paths': {'local_containers': config.get('paths', 'container.dir'),
                      'network_containers': config.get('paths', 'network.dir'),
                      'unzip': config.get('paths', 'unzip.dir'),
                      'log': config.get('paths', 'log.dir'),
                      'history': config.get('paths', 'history.dir'),
                      'failed': config.get('paths', 'failed.dir'),
                      'user_db':config.get('paths', 'user_database.dir')},

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

    ############################# User Penalty #############################
    # A Series of APIs for calculating user penalty
    # 'dopq_history' is an object of DoPQHandler class
    ########################################################################

    def set_dopq_history(self, history):
        self.dopq_history = history

    def get_user_oh(self, user_name):
        user_oh = [int(self.get_user(el) == user_name.lower()) for el in self.dopq_history]
        return np.array(user_oh)

    def calc_exp_decay(self):
        decay = [np.exp(-i) for i in range(len(self.dopq_history))]
        return np.array(decay)

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

    def calc_penalty(self, user_name):
        user_oh = self.get_user_oh(user_name)
        return np.sum(user_oh * self.calc_exp_decay())

    def show_penalties(self, docker_users, history_list):
        for user in docker_users:
            print("Penalty for {}: {}".format(user, round(self.calc_penalty(user), 4)))



    @staticmethod
    def container_freq_for_user(user, container_list):
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

    def print_mapping_dict(self, mapping_dict):
        for key, val in mapping_dict.items():
            print("Key: ", key)
            print("Value[0] : ", val[0])
            print("Size of List: ", len(val[1]))
