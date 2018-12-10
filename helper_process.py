import multiprocessing as mp


class HelperProcess(object):

    def __init__(self):

        self.process = None

    def start(self, target):
        self.process = mp.Process(target=target)
        self.process.start()

        return self.process.pid

    def stop(self):
        if type(self.process) is mp.Process:
            self.process.terminate()

    @property
    def status(self):

        if not type(self.process) is mp.Process: return 'not started'

        if self.process.is_alive():
            return 'running'
        else:
            return 'terminated'
