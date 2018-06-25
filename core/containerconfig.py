#!/usr/bin/env python
# encoding: utf-8
"""
containerconfig.py

Provides a configuration wrapper for container objects.
"""

import json

from utils import log


LOG = log.get_module_log(__name__)


class ContainerConfig:

    def __init__(self, executor_name, num_gpus, num_slots, required_memory, build_flag=True, run_params=None):
        self.executor_name = executor_name
        self.required_memory = required_memory
        self.num_gpus = num_gpus
        self.num_slots = num_slots
        self.build_flag = build_flag
        self.run_params = run_params if run_params is not None else dict()

    @staticmethod
    def from_dict(config_dict):
        """
        Creates a container config instance using given dictionary.

        :param config_dict: Dictionary to build config from.
        :return: ContainerConfig instance if valid config is provided, otherwise None
        """
        executor_name = config_dict.get('executor_name')
        required_memory = config_dict.get('required_memory', '20g')
        num_gpus = config_dict.get('num_gpus', 1)
        num_slots = config_dict.get('num_slots', 1)
        build_flag = config_dict.get('build_flag', True)
        run_params = config_dict.get('run_params')

        # ensure that the executor name is available
        if executor_name is None:
            LOG.error("The name of the executor has to be provided! Anonymous execution is prohibited!")
            return None

        if len(executor_name) < 3:
            LOG.error("The name of the executor has to be at least 3 characters long!")
            return None

        # create instance
        return ContainerConfig(executor_name=executor_name, required_memory=required_memory, num_gpus=num_gpus,
                               num_slots=num_slots, build_flag=build_flag, run_params=run_params)

    @classmethod
    def from_string(cls, json_str):
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load(cls, file_path):
        """
        Loads a container config instance from given file path (expected to be json dump).

        :param file_path: Path to config file (json)
        :return: ContainerConfig instance.
        """

        # read to dict
        with open(file_path, 'r') as file_h:
            config_dict = json.load(file_h)

        return cls.from_dict(config_dict)

    def to_dict(self):
        """
        Creates a dictionary out of current container config instance

        :return: ContainerConfig instance.
        """

        return {'executor_name': self.executor_name,
                'required_memory': self.required_memory,
                'num_gpus': self.num_gpus,
                'num_slots': self.num_slots,
                'build_flag': self.build_flag,
                'run_params': self.run_params}

    def save(self, file_path):
        """
        Serializes current instance to given json file.

        :param file_path: Path to json file.
        :return: None
        """

        # create dict
        config_dict = self.to_dict()

        # dump to file
        with open(file_path, 'w') as file_h:
            json.dump(config_dict, file_h)

    def docker_params(self, image, detach, mounts, environment=[]):
        """
        Build docker params from config and given parameters. Will perform a merge operation, if overlap exists.

        For details of docker run config parameters look at:
        [Docker config]
        (http://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run)

        :param image: Image name
        :param detach: Whether to run in detached mode (instant return)
        :param mounts: Mount configuration.
        :param environment: Environment variables.
        :return: Dictionary which can be passed as kwargs to client.containers.run
        """
        docker_params = self.run_params.copy()

        # fix mem limit
        mem_limit = str(self.required_memory)
        if not mem_limit.lower().endswith('g'):
            LOG.warning("Memory limit should also be in GB (with 'g' suffix)!")
            mem_limit = "{}g".format(mem_limit)

        # add default build parameters
        build_params = {'mem_limit': mem_limit,
                        'image': image,
                        'detach': detach}
        docker_params.update(build_params)

        # add or update mounts
        if 'mounts' in docker_params:
            docker_params['mounts'].update(mounts)
        else:
            docker_params['mounts'] = mounts

        # add or update environment
        if 'environment' in docker_params:
            docker_params['environment'].update(environment)
        else:
            docker_params['environment'] = environment

        # return params
        return docker_params
