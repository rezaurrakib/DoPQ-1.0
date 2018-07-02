import helper_process
from core import container, containerconfig
import utils.gpu
import time
import utils.interface


class DummyDoPQ(helper_process.HelperProcess):

    def __init__(self):
        super(DummyDoPQ, self).__init__()
        self.running_containers = [DummyContainer()]*3
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
        def container_stats(self, runtime_stats=True):
            import psutil

            # build base info
            base_info = {'name': 'dummy', 'executor': 'dummy the dummy', 'run_time': 'forever'}

            # also show runtime info?
            if runtime_stats:

                # cpu_stats = stats_dict['cpu_stats']
                cpu_usage_percentage = psutil.cpu_percent()

                # calc memory usage
                mem_stats = {'usage': 20, 'limit': 100}
                mem_usage = mem_stats['usage'] * 100.0 / mem_stats['limit']

                # add base runtime info
                base_info['cpu_mem'] = {'cpu': cpu_usage_percentage, 'memory': mem_usage}

                # add gpu info, if required
                gpu_info = utils.gpu.get_gpu_infos(0)
                base_info['gpu'] = [
                    {'id': gpu_dt['id'], 'usage': gpu_dt['memoryUsed'] * 100.0 / gpu_dt['memoryTotal']}
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


