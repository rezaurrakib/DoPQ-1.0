import time
import datetime
import subprocess
import multiprocessing as mp

__authors__ = "Ilja Manakov, Markus Rohm"


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
        if self.status == 'running':
            self.process.terminate()

    @property
    def status(self):

        if not isinstance(self.process, mp.Process):
            return 'not started'

        if self.process.exitcode is None:
            return 'running'
        else:
            return 'terminated'

    @property
    def uptime(self):

        pid = self.process.pid
        # initiate process that find the process by pid and writes uptime to standard output
        proc = subprocess.Popen(['ps', '-p', '{}'.format(pid), '-o', 'etime='], stdout=subprocess.PIPE)
        proc.wait()

        # retrive uptime from standard output
        uptime = "".format(proc.stdout.readlines()[0].strip())

        # check if uptime contains days
        uptime = uptime.split('-')
        if len(uptime) > 1:
            days = int(uptime[0])
            uptime = uptime[1]
        else:
            days = 0
            uptime = uptime[0]

        # split uptime into hours, minutes and seconds
        uptime = uptime.split(':')
        if len(uptime) == 2:  # if process has not been running for at least one hour
            hours = 0
            minutes = int(uptime[0])
            seconds = int(uptime[1])
        elif len(uptime) > 2:
            hours = int(uptime[0])
            minutes = int(uptime[1])
            seconds = int(uptime[2])
        else:
            hours = 0
            minutes = 0
            seconds = 0

        # convert information to print format
        uptime = ''
        uptime += '{}d '.format(days) if days else ''
        uptime += '{}h '.format(hours) if hours else ''
        uptime += '{}m '.format(minutes) if minutes else ''
        uptime += '{}s '.format(seconds) if not minutes else ''

        # get the start time
        uptime_in_seconds = days * 24 * 3600 + hours * 3600 + minutes * 60 + seconds
        starttime = time.time() - uptime_in_seconds
        starttime = datetime.datetime.fromtimestamp(starttime).strftime("%a, %d.%b %H:%M")

        return uptime, starttime
