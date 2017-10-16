#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
======================================================
***         Docker Priority Queue (DoP-Q)          ***
======================================================

    |Purpose: Priority queue to run docker containers

Created on Mon May 29 23:21:42 2017

History:
    16.10.2017: Changed to python 2.7

@author: markus
"""

import os
import numpy as np
from functools import partial
import subprocess
import docker
import zipfile
import logging
import time
import shutil
# import configparser # python 3
import ConfigParser  # python 2
import re

# import requests

CONFIG_FILE = 'config.ini'


def init_file_logging(log_file_path, log_level=logging.DEBUG):
    """
    Init basic logging
    :param log_file_path: Path to logfile
    :param log_level: Logging level to use
    :return: None
    """
    logging.basicConfig(filename=log_file_path, level=logging.DEBUG)


def handle_invalid_containers(container_path, valid_executors, auto_remove_invalid=False):
    """
    Will detect invalid containers and create a warning in log and if flag is set, also delete the correspnding
    containers.
    :param container_path: Path to containers
    :param valid_executors: Valid executors
    :param auto_remove_invalid: If true invalid containers will be removed
    :return: None
    """
    # check for invalid files and warn
    invalid_docker_files = [el for el in os.listdir(container_path) if
                            el.split('.')[0].split('_')[-1].lower() not in valid_executors and not len(
                                valid_executors) == 0]
    if len(invalid_docker_files) > 0:
        logging.warning(
            "*** WARNING ***: The following containers are provided by persons, who are not authorized to run "
            "containers on this machine: {}".format(
                invalid_docker_files))
        if auto_remove_invalid:
            for filename in invalid_docker_files:
                file_path = os.path.join(container_path, filename)
                logging.warning("\nRemoving {}".format(file_path))
                os.remove(file_path)


def get_user_oh(user_name, docker_history):
    user_oh = [int(el == user_name.lower()) for el in docker_history]
    return np.array(user_oh)


def calc_exp_decay(docker_history):
    decay = [np.exp(-i) for i in range(len(docker_history))]
    return np.array(decay)


def calc_penalty(user_name, docker_history):
    user_oh = get_user_oh(user_name, docker_history)
    return np.sum(user_oh * calc_exp_decay(docker_history))


def extract_user_from_filename(filename):
    user = filename.split('.')[0].split('_')[-1]
    return user.lower()


def split_and_calc_penalty(filename, docker_history):
    user = extract_user_from_filename(filename)
    return calc_penalty(user, docker_history)


def show_penalties(docker_users, docker_history):
    for user in docker_users:
        print("Penalty for {}: {}".format(user, round(calc_penalty(user, docker_history), 4)))


# Interesting stuff here. If nvidia-docker is running you access information about
# gpu devices by running get requests on local host.
# def get_gpu_devices(request_url="http://localhost:3476/gpu/info/json"):
#    r = requests.get(request_url)
#    json_data = r.json()
#    gpu_ids = [dev['UUID'] for dev in json_data['Devices']]
#    return gpu_ids


def get_gpu_minors():
    """
    Returns the GPU minors available on the system
    :return: GPU minors available on the system
    """
    minors = []
    for dev in os.listdir("/dev"):
        match_dt = re.search(r'nvidia(\d+)', dev)
        if not match_dt is None:
            minor = int(match_dt.group(1))
            minors.append(minor)
    return minors


def get_loaded_images(out):
    """
    Extracts the loaded images from the output of docker load
    :param out: Output text of docker load
    :return: Loaded images as list
    """
    # build matcher
    img_matcher = re.compile(r'Loaded image: (.*)?')

    loaded_images = []

    # get the name of the image
    for out_line in out.splitlines():
        img_match_dt = img_matcher.search(out_line)
        if img_match_dt is not None:
            img = img_match_dt.group(1)
            loaded_images.append(img)

    return loaded_images


def get_assigned_gpu_minors(client):
    """
    Looks at each running container and extracts the minors of the GPUs used there
    :param client: docker-client
    :return: Minors of all GPUs assigned to some container
    """

    # get assigned gpus
    assigned_gpus = set()

    # look in each running container
    for container in client.containers.list():

        if 'HostConfig' in container.attrs:
            if 'Devices' in container.attrs['HostConfig']:
                for el in container.attrs['HostConfig']['Devices']:
                    host_path = el['PathOnHost']
                    match_dt = re.search(r'/dev/nvidia(\d+)', host_path)
                    if match_dt is not None:
                        gpu_minor = int(match_dt.group(1))
                        assigned_gpus.add(gpu_minor)

    return assigned_gpus


def get_free_gpu_minors(client):
    """
    Returns all minors which are currently not used.
    :param client: docker-client
    :return: Unused GPU minors
    """

    # get assigned gpus
    assigned_gpus = get_assigned_gpu_minors(client)

    # get all gpus
    available_gpus = get_gpu_minors()

    free_gpus = []

    # remove all assigned
    for gpu_minor in available_gpus:

        # only add unassigend ones
        if gpu_minor not in assigned_gpus:
            free_gpus.append(gpu_minor)

    return free_gpus


def run_queue(config, verbose=True):
    """
    Runs the priority queue.

    TBD: Save history later. For now just create a empty one
    config: Configuration to use
    verbose: Will provide verbose output, if true
    :return: None
    """

    # init logging
    init_file_logging(config.get('reporting', 'log.path'))

    # show init
    logging.info("Setting up DoP-Q..")

    # init api
    client = docker.from_env()

    # create empty history
    docker_history = []

    # get acquire paths from config
    container_files_path = config.get('queue', 'container.path')
    build_directory = config.get('queue', 'build.directory')
    load_directory = config.get('queue', 'load.directory')
    valid_executors = config.get('queue', 'valid_executors').split(',')
    max_history = config.getint('queue', 'max.history')
    auto_remove_invalid = config.getboolean('queue', 'remove.invalid.containers')
    max_gpu_assignment = config.getint('gpu', 'max.assignment')

    # build all non-existent directories
    for dir_path in [build_directory, load_directory, container_files_path]:
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

    # run this until forced to quit
    while True:

        # get docker files
        docker_files = [os.path.join(container_files_path, el) for el in os.listdir(container_files_path) if
                        el.split('.')[0].split('_')[-1].lower() in valid_executors or len(valid_executors) == 0]

        # handle invalid containers
        handle_invalid_containers(container_files_path, valid_executors, auto_remove_invalid=auto_remove_invalid)

        # get free gpus
        free_gpus = get_free_gpu_minors(client)

        # can we run another container?
        if len(free_gpus) == 0:

            # we're full, just wait
            time.sleep(5)

        else:

            # true if we successfully run one container from the currently available ones
            successfully_dequeued_one = False

            # try as long as we have available containers and as long we could not dequeue a single container
            while len(docker_files) > 0 and not successfully_dequeued_one:

                # sort priority queue:
                sort_fn = partial(split_and_calc_penalty, docker_history=docker_history)
                docker_files = sorted(docker_files, key=sort_fn)
                # print(docker_files)

                # pick first
                file_to_run_source_path = docker_files.pop(0)

                # get parts
                container_source_folder, container_source_filename = os.path.split(file_to_run_source_path)

                # should we build a container?
                if container_source_filename.lower().startswith(
                        'build_') and container_source_filename.lower().endswith('.zip'):

                    # build target folder
                    container_target_folder = os.path.join(build_directory, container_source_filename[:-4])

                    try:

                        # report
                        logging.info("Unzipping {} to {}".format(file_to_run_source_path, container_target_folder))

                        # open zip file
                        z = zipfile.ZipFile(file_to_run_source_path)

                        # extract all
                        z.extractall(container_target_folder)

                        # close archive
                        z.close()

                        # build image name
                        container_image_name = "dbsifi/dl_{}:latest".format(
                            container_source_filename[6:-4].replace(' ', ''))

                        logging.info("Container-Image: {}".format(container_image_name))

                        # run command
                        p = subprocess.Popen(["nvidia-docker", "build", "-t", "{}".format(container_image_name),
                                              container_target_folder])
                        p.communicate()  # wait till done

                        build_success = p.returncode == 0

                        if not build_success:
                            # pass on to log file
                            logging.error("Unable to build given docker file"
                                          ": {}, response-code={}".format(container_image_name, p.returncode))

                        # wait a second (just to be sure that the archive is closed)
                        time.sleep(1)

                        # report
                        logging.info("All done. Cleaning up..".format(file_to_run_source_path, container_target_folder))

                        # remove the container
                        os.remove(file_to_run_source_path)

                        # clean up build directory
                        shutil.rmtree(container_target_folder)

                        # set flag
                        successfully_dequeued_one = build_success

                    except Exception as ex:

                        # report problem
                        logging.error(
                            "An execption occured while trying to build the container ({}): {}. Maybe the container"
                            " is still copied, while trying accessing it. Will try again later".format(
                                container_source_filename, ex))

                else:

                    try:

                        # build target path
                        file_to_run_target_path = os.path.join(load_directory, container_source_filename)

                        # try to move the file
                        shutil.move(file_to_run_source_path, file_to_run_target_path)

                        # wait a second (just to be sure that system had enough time to
                        # close the file handle after moving)
                        time.sleep(1)

                        # try to load the file
                        p = subprocess.Popen(["nvidia-docker", "load", "--input", file_to_run_target_path])
                        out, _ = p.communicate()  # wait till done

                        if p.returncode == 0:

                            # get loaded images
                            loaded_images = get_loaded_images(out)

                            # verify
                            if len(loaded_images) > 0:

                                # warning if more than one
                                if len(loaded_images) > 1:
                                    logging.warning(
                                        "We found more than one image in container {}. However, we will only run "
                                        "the last one. Please provide containers which only expose a single "
                                        "image.".format(container_source_filename))

                                # use the latest found image
                                container_image_name = loaded_images[-1]

                                # set success flag
                                successfully_dequeued_one = True

                            else:

                                logging.error("We were not able to load a single image from container "
                                              "{}".format(container_source_filename))

                        else:

                            logging.error("Unable to load the container image from"
                                          " file {}".format(container_source_filename))

                    except Exception as ex:

                        # report problem
                        logging.error("An exception occurred while trying to load the container ({}): {}. Maybe the "
                                      "container is still copied, while trying accessing it. Will try again"
                                      " later".format(container_source_filename, ex))

                # successful?
                if successfully_dequeued_one:
                    # ensure valid
                    assert (container_image_name is not None)

                    # get gpu assignment
                    gpu_assignment = free_gpus[:max_gpu_assignment]

                    # report
                    logging.info("\n*** Running docker image {}\n".format(container_image_name))

                    # run the container (detached mode, remove afterwards)
                    docker_env = os.environ.copy()
                    docker_env["NV_GPU"] = ','.format(gpu_assignment)

                    # if the -rm flag is add, the run is not visible with docker -ps && docker -ls
                    p = subprocess.Popen(["nvidia-docker", "run", "-d", container_image_name],
                                         env=docker_env)
                    p.communicate()  # wait till done

                    # add to log fil whether it was successful
                    logging.info("Result from nvidia-docker run: {}".format(p.returncode))

                    # add to history
                    docker_history = [extract_user_from_filename(container_source_filename)] + docker_history
                    docker_history = docker_history[:max_history]

            else:

                # wait 5 seconds (do not write this to log file, we do not want to blow it up!)
                if verbose:
                    print("Nothing there to do.. So boring here, I take some rest.. :-(")
                time.sleep(5)


def write_default_config():
    """
    Write default configuration
    :return: None
    """

    config = ConfigParser.ConfigParser()

    config.add_section('queue')
    config.set('queue', 'container.path', 'docker_containers')
    config.set('queue', 'load.directory', 'docker_load')
    config.set('queue', 'build.directory', 'docker_build')
    config.set('queue', 'max.history', '100')
    config.set('queue', 'remove.invalid.containers', 'yes')
    config.set('queue', 'valid_executors', 'anees,ilja,ferry,markus')

    config.add_section('reporting')
    config.set('reporting', 'log.path', 'queue.log')
    config.set('reporting', 'verbose', 'yes')

    config.add_section('gpu')
    config.set('gpu', 'max.assignment', '1')

    # store config
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def read_config():
    # create config parser and read file
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    return config


def main(argv=None):
    # create new config if not there
    if not os.path.isfile(CONFIG_FILE):
        write_default_config()

    # read in config
    config = read_config()

    # get verbosity flag
    verbose = config.getboolean('reporting', 'verbose')

    # run the queue
    run_queue(config, verbose)

    # leave
    return 0  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)
