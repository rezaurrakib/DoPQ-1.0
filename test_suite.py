import helper_process
from core import container, containerconfig
import utils.gpu
import time
import utils.interface
import numpy as np
from utils.cpu import CPU

class DummyDoPQ(helper_process.HelperProcess):

    def __init__(self):
        super(DummyDoPQ, self).__init__()
        self.running_containers = [DummyContainer('dummy', [0]),
                                   DummyContainer('dummy', [1], 'Sir Dummington'),
                                   DummyContainer('dummy', [2, 0], 'lazy_dummy_420', 'paused'),
                                   DummyContainer('dummy', [1], 'Much Container! WOW!', 'exited')]
        self.provider = DummyProvider()
        self.user_list = ['dummy the dummy', 'simple dummy', 'Sir Dummington', 'dummy with no name']#,
                          #'360_no_dummy', 'swag_dummy', 'bla', 'last_one']

        self.history = self.generate_container_list(100)
        self.container_list = self.generate_container_list(100)

    def generate_container_list(self, n):
        containers = []
        for i in range(n):
            user = self.user_list[np.random.randint(0, len(self.user_list))]
            containers.append(DummyContainer(user))
        return containers

    def run_queue(self):
        try:
            while not self.term_flag.value:

                time.sleep(10)
        finally:
            self.provider.stop()
            self.stop()

    def start(self):
        super(DummyDoPQ, self).start(target=self.run_queue, name='DummyQueue')
        utils.interface.run_interface(self)

    @property
    def users_stats(self):
        users = self.user_list
        user_stats = []

        # get info for all users
        for user in users:
            single_user_stats = {'user': user,
                                 'penalty': round(np.random.randn(1), 4),
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


class DummyContainer(object):

    def __init__(self, user, minors=[], name='dummy', status='running'):

        self.minors = minors
        self.name = name
        self.status = status
        self.user = user

    @property
    def use_gpu(self):
        return bool(self.minors)

    @property
    def docker_name(self):
        return 'mighty_mckenzie'

    def container_stats(self, runtime_stats=True):
        import psutil

        # build base info
        base_info = {'name': self.name, 'executor': self.user, 'run_time': 'forever', 'created': 'ancient times',
                     'docker name': self.docker_name, 'status': self.status}

        # also show runtime info?
        if runtime_stats:

            # cpu_stats = stats_dict['cpu_stats']
            cpu = CPU(interval=0.1)
            cpu_usage_percentage = cpu.cpu_percent()

            # calc memory usage
            mem_stats = {'usage': 20, 'limit': 100}
            mem_usage = mem_stats['usage'] * 100.0 / mem_stats['limit']

            # add base runtime info
            base_info.update({'cpu': cpu_usage_percentage, 'memory': mem_usage})

            # add gpu info, if required
            gpu_info = {}
            for minor in self.minors:
                gpu_info[str(minor)] = {'id': minor, 'usage': np.random.randint(0, 100)}

            base_info['gpu'] = [
                {'id': gpu_dt['id'], 'usage': gpu_dt['usage']}
                for gpu_dt in gpu_info.values()]

        return base_info


class DummyProvider(helper_process.HelperProcess):

    def __init__(self):
        super(DummyProvider , self).__init__()
        self.start()

    def provide(self):
        while not self.term_flag.value:
            time.sleep(10)

    def start(self):
        super(DummyProvider, self).start(target=self.provide, name='DummyProvider')


if __name__ == '__main__':

    dopq = DummyDoPQ()
    dopq.start()


