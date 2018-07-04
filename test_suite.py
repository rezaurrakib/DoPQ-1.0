import helper_process
from core import container, containerconfig
import utils.gpu
import time
import utils.interface
import numpy as np


class DummyDoPQ(helper_process.HelperProcess):

    def __init__(self):
        super(DummyDoPQ, self).__init__()
        self.running_containers = [DummyContainer([0]),
                                   DummyContainer([1], 'Sir Dummington'),
                                   DummyContainer([2, 0], 'lazy_dummy_420', 'paused'),
                                   DummyContainer([1], 'Much Container! WOW!', 'exited')]
        self.provider = DummyProvider()

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


class DummyContainer(object):

    def __init__(self, minors=[], name='dummy', status='running'):

        self.minors = minors
        self.name = name
        self.status = status

    @property
    def use_gpu(self):
        return bool(self.minors)

    @property
    def docker_name(self):
        return 'mighty_mckenzie'

    def container_stats(self, runtime_stats=True):
        import psutil

        # build base info
        base_info = {'name': self.name, 'executor': 'dummy the dummy', 'run_time': 'forever', 'created': 'ancient times',
                     'docker name': self.docker_name, 'status': self.status}

        # also show runtime info?
        if runtime_stats:

            # cpu_stats = stats_dict['cpu_stats']
            cpu_usage_percentage = psutil.cpu_percent()

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


