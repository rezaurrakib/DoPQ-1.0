import docker
import multiprocessing as mp
import logging
import os
import time


class CHException(Exception):
    pass


class ContainerHandler(object):

    def __init__(self, config):
        """
        class for handling and running docker containers from the priority queue
        :param config: dict as created by parse_config() in dop_q.py
        """
        self.client = docker.from_env()
        self.config = config['docker']
        self.paths = config['paths']
        self.mounts = self.config.pop('mounts', None)
        self.logging_interval = self.config.pop('logging_interval', 1)
        self.processes = []
        self.containers = []

    @property
    def running_containers(self):
        """
        small wrapper function to the docker api
        :return: list of currently running containers on the docker client
        """
        return self.client.containers.list()

    @staticmethod
    def create_mounts(mount_list, user):
        """
        converts string to docker.type.Mount objects, also automatically adds user folder to /outdir
        :param mount_list: list of docker mount strings (as given in the config.ini)
        :param user: user for whom the mounts are created
        :return: list of docker.types.Mount objects, same len as mount_list
        """

        if mount_list == ['']: return None

        mounts = []
        for mount in mount_list:

            # split mount string in source and target
            mount = mount.split(':')

            # append user folder to source if target is outdir
            if mount[1] == '/outdir': mount[0] = os.path.join(mount[0], user)
            if not os.path.exists(mount[0]): os.makedirs(mount[0])

            # create Mount object and append to list
            mount = docker.types.Mount(source=mount[0], target=mount[1], type='bind')
            mounts.append(mount)

        return mounts

    def run_container(self, image, user, gpu_minors, command=None):
        """
        method for running docker containers
        :param image: image from which a container is created
        :param user: user whom the container belongs to
        :param gpu_minors: gpu minor(s) that will be made visible to the container
        :param command: command that will be run inside the container (default=None)
        :return: logging process, docker container
        """
        try:
            # append user dir to outdir
            mounts = self.create_mounts(self.mounts, user)

            # create the container
            container = self.client.containers.create(image=image, command=command, detach=True, mounts=mounts,
                                                      environment=["NVIDIA_VISIBLE_DEVICES="+str(gpu_minors)],
                                                      **self.config)

            # log start time and start container
            start_time = int(time.time())
            container.start()
            self.containers.append(container)

            # start process that gets container logs and writes them to a logfile
            p = mp.Process(target=self.monitor_container_logs, args=(container, user, image, start_time))
            p.start()
            self.processes.append(p)

            return p, container

        except Exception as e:

            # just so it's clear that the Exception came from this class
            raise CHException(e)

    def monitor_container_logs(self, container, user, image, start_time):
        """
        method that fetches container logs and writes them to a logfile, runs as long as container is running
        :param container: container for which to write logs
        :param user: user whom the container belongs to
        :param image: image from which the container is created
        :param start_time: time at which the container was started
        :return: None
        """

        # initialize logging for the container
        logfile = os.path.join(self.paths['log'], user)
        if not os.path.isdir(logfile): os.makedirs(logfile)
        logfile = os.path.join(logfile, image + '.log')
        logger_name = user + '_' + image
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.FileHandler(logfile))

        # update container
        container.reload()

        # periodically write container logs to logfile
        last_check = start_time
        while container.status == 'running':

            # wait set time before getting logs
            time.sleep(self.logging_interval)

            # get logs and update chekpoint time
            new_logs = container.logs(since=last_check)
            last_check = int(time.time())

            # write logs and update container
            logger.info(new_logs)
            container.reload()

        # write remaining logs, when container has finished
        else:
            new_logs = container.logs(since=last_check)
            logger.info(new_logs)


# some testing
if __name__ == '__main__':
    import dop_q

    path = '/home/kazuki/Documents/Promotion/Projects/dop-q/test/invalid/config.ini'
    config = dop_q.parse_config(path)
    chandler = ContainerHandler(config)
    p, container = chandler.run_container('tf-base', 'imanakov', 'all', 'nvidia-smi')
    print('done')

