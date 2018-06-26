#!/usr/bin/env python
# encoding: utf-8
"""
gpu.py

Helpers for GPU information retrieval
"""

import docker


def get_system_gpus():
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


def get_assigned_gpus(client=None):
    """
    Updates assigned and free minors by looking at the running containers

    :param client: Docker API client.
    :return: None
    """

    # if there is no client
    if client is None:

        # get a client
        client = docker.from_env()

    # get assigned gpus
    assigned_gpus = []

    # look in each running container
    for container in client.containers.list():

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
                                gpu_minor = int(gpu_minor)
                                if gpu_minor in self.minors:
                                    assigned_gpus.append(gpu_minor)

    return assigned_gpus


def get_gpus_status(client=None):
    """
    Get free GPU minors.

    :param client: Docker API client.
    :return: A list with free GPU minors.
    """

    assigned_gpus = get_assigned_gpus(client)
    free_gpus = []

    # remove all assigned
    for gpu_minor in get_system_gpus():

        # only add unassigend ones
        if gpu_minor not in assigned_gpus:
            free_gpus.append(gpu_minor)

    return free_gpus, assigned_gpus
