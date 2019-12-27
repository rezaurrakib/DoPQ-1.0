import time
import psutil


class CPU(object):
    """
    singleton class for fetching cpu usage percentage
    psutil will not return sensible results if called to quickly in succesion, this class is meant to be a solution to this
    """

    class __CPU(object):

        def __init__(self, interval):
            self.last_call = 0
            self.usage = 0
            self.interval = interval

        def cpu_percent(self):
            current_time = time.time()

            if current_time - self.last_call > self.interval:
                self.usage = psutil.cpu_percent()
                self.last_call = current_time

            return self.usage

    instance = None

    def __init__(self, interval):

        if CPU.instance is None:
            CPU.instance = CPU.__CPU(interval)
        else:
            CPU.instance.interval = interval

    def cpu_percent(self):
        return CPU.instance.cpu_percent()
