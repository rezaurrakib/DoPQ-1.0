#!/usr/bin/env python
# encoding: utf-8
"""
containerconfig.py

Provides a configuration wrapper for container objects.
"""

import os
import zipfile

from core.containerconfig import ContainerConfig
from utils import log


LOG = log.get_module_log(__name__)


def parse_unzipped_config(folder_path, config_filename="container_config.json"):
    """
    Reads a container configuration from a given (unzipped) folder path.
    :param folder_path: Path to folder, which contains all container files.
    :param config_filename: File name for configuration file.
    :return: ContainerConfig instance if successful, otherwise None
    """

    # build path
    file_path = os.path.join(folder_path, config_filename)

    # ensure that path exists
    if not os.path.isfile(file_path):
        LOG.error("Invalid docker container setup found: No configuration file "
                  "({}) could be found!".format(config_filename))
        return None

    # read in config
    return ContainerConfig.load(file_path)


def parse_zipped_config(zip_path, config_filename="container_config.json"):
    """
    Reads container configuration directly from zipped docker file. Automatically retrieves the configuration even
    from subfolders (if unambiguous).

    :param zip_path: Path to zip file.
    :param config_filename: Name of the config file.
    :return: ContainerConfig instance if successful, otherwise None
    """

    with zipfile.ZipFile(zip_path) as zip_h:

        # directly packed?
        if config_filename in zip_h.namelist():
            return ContainerConfig.from_string(zip_h.read(config_filename))

        # get candidates
        candidates = [name_i for name_i in zip_h.namelist() if name_i.endswith(config_filename)]

        # should be unique
        if len(candidates) != 1:
            LOG.error("The required configuration file '{}' is not available or ambiguous (found={})! "
                      "Please provide a single file with this name or place it to root folder.".format(config_filename,
                                                                                                       len(candidates)))
            return None

        # load candidate
        return ContainerConfig.from_string(zip_h.read(candidates[0]))
