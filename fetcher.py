"""
small script for monitoring the amount of containers on the local drive and 
fetching new ones if needed.
This script is intended to be called from run.py with the relevant paths passed
as command line arguments.
"""

import sys
import os
import shutil
import logging
import time
import ctypes
import numpy as np



def get_free_space(path, log_dir):
    """
    helper function for examining free space on a drive
    --------------
    args:
        - path: directory that should be examined
    return: 
        - free_space_abs: absolute amount of free space in bytes
        - free_space_rel: percentage of available free space
    """

    # initialize return variables
    free_space_abs, free_space_rel = 0, 0

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

    logging.info(
        time.ctime() + "\tFree space on hard drive: " + str(int(free_space_abs / 1024 / 1024)) + "MB which is " + \
        str(round(free_space_rel * 100, 2)) + "%")
    return free_space_abs, free_space_rel


def move_containers(network_containers, network_dir, local_dir):
    """
    helper function for moving containers from network share to local drie
    --------------
    args:
        - network_containers: list of the container names that should be moved
        - network_dir: directory on the network share that hold the containers (source)
        - local_dir: directory on the local drive where the containers should be moved to (destination)
    """

    # write to log
    logging.info(time.ctime() + ":\tFetching containers form network drive.")
    logging.info("---------------------------------------------------------")

    for container in network_containers:
        # move files
        shutil.move(os.path.join(network_dir, container), local_dir)

        # log containers that have been moved
        logging.info(time.ctime() + ":\tMoved container {} from network to local drive.".format(container))

    # write LF to log for better readability
    logging.info("\n")


def run_fetcher(local_dir, network_dir, log_dir):

    # set up logging
    LOG_FILE = os.path.join(log_dir, "container_fetcher.log")
    logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)

    # write passed directories to log
    logging.info(time.ctime() + "\tpassed directories:\n\t\tlocal hard drive:\t" + local_dir
                 + "\n\t\tshared network drive:\t" + network_dir
                 + "\n\t\tlog-file path:\t\t" + log_dir)

    # control variable for while loop
    first_run = True

    ##get number of containers present on the hard drive
    # num_local_containers = len(os.listdir(local_dir))

    # start monitoring loop
    while 1:

        # wait for 1h from the second iteration onward before fetching containers
        if not first_run:
            time.sleep(36000)
        else:
            first_run = not first_run

        # check if enough space is present on hard drive
        free_space_abs, free_space_rel = get_free_space(local_dir, log_dir)
        if free_space_rel < 0.05:
            logging.info(time.ctime() + "\tnot enough space to fetch new containers")
            continue

        # get list of containers on network drive
        network_containers = os.listdir(network_dir)

        # check if any containers are on the network drive
        if len(network_containers) == 0:
            logging.info(time.ctime() + "\tno containers to fetch")
            continue

        # get filesizes of the network containers
        network_containers_sizes = [os.stat(os.path.join(network_dir, container)).st_size for container in
                                    network_containers]

        # check if there is enough space to move all files
        if np.sum(network_containers_sizes) < free_space_abs:
            # move containers
            move_containers(network_containers, network_dir, local_dir)
            continue

        # remove files until they fit on the hard drive
        logging.info(time.ctime() + "\tnot enough space to fetch all containers...fetching only a part of them")

        # clone lists for modification
        tmp_network_containers = network_containers
        tmp_network_containers_sizes = network_containers_sizes

        # iteratively remove containers
        while np.sum(tmp_network_containers_sizes) > free_space_abs:
            tmp_network_containers.pop()
            tmp_network_containers_sizes.pop()
            if len(tmp_network_containers) == 1:
                if tmp_network_containers_sizes[0] > free_space_abs:
                    continue
                else:
                    break

        # move containers
        move_containers(network_containers, network_dir, local_dir)
        continue

if __name__ == "__main__":

    # get directories from console args
    local_dir, network_dir, log_dir = sys.argv[1:4]
    run_fetcher(local_dir,network_dir,local_dir)
