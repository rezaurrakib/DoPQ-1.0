import multiprocessing as mp


class HelperProcess(object):

    def __init__(self):

        self.process = None
        self.term_flag = mp.Value('i', 0)

    def start(self, target, name='HelperProcess'):
        self.process = mp.Process(target=target, name=name)
        self.process.start()

        return self.process.pid

    def stop(self):
        self.term_flag.value = 1
        if type(self.process) is mp.Process:
            self.process.terminate()

    @property
    def status(self):

        if not type(self.process) is mp.Process: return 'not started'

        if self.process.exitcode is None:
            return 'running'
        else:
            return 'terminated'