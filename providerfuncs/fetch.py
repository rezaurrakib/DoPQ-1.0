"""
small script for monitoring the amount of containers on the local drive and
fetching new ones if needed.
This script is intended to be called from run.py with the relevant paths passed
as command line arguments.
"""

import os
import shutil
import time
import ctypes
import numpy as np


def get_free_space(path, logger):
    """
    helper function for examining free space on a drive
    --------------
    args:
        - path: directory that should be examined
    return:
        - free_space_abs: absolute amount of free space in bytes
        - free_space_rel: percentage of available free space
    """

    # check if windows or unix
    if os.name == "nt":
        free_bytes, total_bytes = ctypes.c_ulonglong(0), ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, ctypes.pointer(total_bytes),
                                                   ctypes.pointer(free_bytes))
        free_space_abs = free_bytes.value
        free_space_rel = free_space_abs / total_bytes.value

    else:
        stat = os.statvfs(path)
        free_space_abs = stat.f_frsize * stat.f_bavail
        total_space = stat.f_frsize * stat.f_blocks
        free_space_rel = float(free_space_abs) / float(total_space)

    logger.info(
        time.ctime() + "\tFree space on hard drive: " + str(int(free_space_abs / 1024 / 1024)) + "MB which is " + \
        str(round(free_space_rel * 100, 2)) + "%")

    return free_space_abs, free_space_rel


def move_containers(container_list, source_dir, target_dir, logger):
    """
    helper function for moving containers from network share to local drive
    --------------
    args:
        - container_list: list of the container names that should be moved
        - source_dir: directory on the network share that hold the containers (source)
        - target_dir: directory on the local drive where the containers should be moved to (destination)
    """

    # write to log
    logger.info(time.ctime() + ":\tFetching containers form {}.".format(source_dir))
    logger.info("---------------------------------------------------------")

    for container in container_list:
        # move files
        shutil.move(os.path.join(source_dir, container), target_dir)

        # log containers that have been moved
        logger.info(time.ctime() + ":\tMoved container {} to {}".format(container, target_dir))

    # write LF to log for better readability
    logger.info("\n")


def handle_invalid_containers(source_dir, users, logger, rm_invalid=False):
    """
    Will detect invalid containers and create a warning in log and if flag is set, also delete the correspnding
    containers.
    :return: None
    """
    # check for invalid files and warn
    invalid_docker_files = [el for el in os.listdir(source_dir)
                            if os.path.isfile(os.path.join(source_dir, el))
                            and el.split('_')[-1].split('.')[0].lower() not in users
                            and not len(users) == 0]

    if len(invalid_docker_files) > 0:
        logger.warning(time.ctime() + ":\t"
                                       "The following containers are provided by persons, who are not authorized to run "
                                       "containers on this machine:\n {}".format(invalid_docker_files))

        if rm_invalid:
            for filename in invalid_docker_files:
                file_path = os.path.join(source_dir, filename)
                os.remove(file_path)
        else:
            invalid_path = os.path.join(source_dir, 'invalid') + '/'
            if not os.path.exists(invalid_path): os.makedirs(invalid_path)
            for filename in invalid_docker_files:
                file_path = os.path.join(source_dir, filename)
                shutil.move(file_path, invalid_path)


def fetch(source_dir, target_dir, logger, min_space=0.05):

    # check if enough space is present on hard drive
    free_space_abs, free_space_rel = get_free_space(target_dir)
    if free_space_rel < min_space:
        logger.info(time.ctime() + "\tnot enough space to fetch new containers")
        return []

    # check if invalid containers are present
    #handle_invalid_containers(source_dir, users, logger, rm_invalid)

    # get list of containers on network drive
    container_list = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]

    # check if any containers are on the network drive
    if len(container_list) == 0:
        logger.info(time.ctime() + "\tno containers to fetch")
        return []

    # get filesizes of the network containers
    container_list_sizes = [os.stat(os.path.join(source_dir, container)).st_size
                            for container in container_list]

    # check if there is enough space to move all files
    if np.sum(container_list_sizes) < free_space_abs:
        # move containers
        move_containers(container_list, source_dir, target_dir, logger)
        return []

    # remove files until they fit on the hard drive
    logger.info(time.ctime() + "\tnot enough space to fetch all containers...fetching only a part of them")

    # clone lists for modification
    tmp_container_list = container_list
    tmp_container_list_sizes = container_list_sizes

    # iteratively remove containers
    while np.sum(tmp_container_list_sizes) > free_space_abs:
        tmp_container_list.pop()
        tmp_container_list_sizes.pop()
        if len(tmp_container_list) == 1:
            if tmp_container_list_sizes[0] > free_space_abs:
                return tmp_container_list
            else:
                return []

    # move containers
    move_containers(container_list, source_dir, target_dir, logger)
    return container_list

