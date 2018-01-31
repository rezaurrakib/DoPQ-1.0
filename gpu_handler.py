import re
import os
import docker


class GPUHandler(object):

    def __init__(self):
        """
        small class for handling gpu minor monitoring
        :param client: docker client as obtained by docker.from_env()
        """
        self.client = docker.from_env()
        self.minors = self.get_gpu_minors()
        self._assigned_minors = []
        self._free_minors = []

    @staticmethod
    def get_gpu_minors():
        """
        Returns the GPU minors available on the system
        :return: GPU minors available on the system
        """
        minors = []
        for dev in os.listdir("/dev"):
            match_dt = re.search(r'nvidia(\d+)', dev)
            if match_dt is not None:
                minor = int(match_dt.group(1))
                minors.append(minor)
        return minors

    @property
    def assigned_minors(self):
        """
        returns currently assigned minors
        :return: currently assigned minors
        """
        self.update_minors()
        return self._assigned_minors

    @property
    def free_minors(self):
        """
        returns currently free minors
        :return: currently free minors
        """
        self.update_minors()
        return self._free_minors

    def update_minors(self):
        """
         updates assigned and free minors by looking at the running containers
         :return: None
         """

        # get assigned gpus
        assigned_gpus = []

        # look in each running container
        for container in self.client.containers.list():

            if 'Config' in container.attrs:
                if 'Env' in container.attrs['Config']:
                    for el in container.attrs['Config']['Env']:
                        if el.startswith('NVIDIA_VISIBLE_DEVICES'):
                            minor_str = el.split('=')[1]
                            if minor_str.lower() == 'all':
                                for gpu_minor in self.minors:
                                    assigned_gpus.append(gpu_minor)
                            # elif minor_str.lower() == 'none':
                            #     # here no minors will be used
                            #     logging.debug("Using no minors..")
                            # elif minor_str.lower() == 'void' or minor_str.trim() == "":
                            #     logging.debug("Insecure option: Please do not use empty minor option for containers!")
                            else:
                                minor_list = minor_str.split(",")
                                for gpu_minor in minor_list:
                                    if gpu_minor in self.minors:
                                        assigned_gpus.append(gpu_minor)

        free_gpus = []

        # remove all assigned
        for gpu_minor in self.minors:

            # only add unassigend ones
            if gpu_minor not in assigned_gpus:
                free_gpus.append(gpu_minor)

        self._assigned_minors = assigned_gpus
        self._free_minors = free_gpus
