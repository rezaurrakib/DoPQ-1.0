#!/usr/bin/env python
# encoding: utf-8
"""
containerconfig.py

Provides a configuration wrapper for container objects.
"""

import os

from core.containerconfig import ContainerConfig


def parse_unzipped_config(folder_path, config_filename="config.json"):
    """
    Reads a container configuration from a given (unzipped) folder path.
    :param folder_path: Path to folder, which contains all container files.
    :param config_filename: File name for configuration file.
    :return: ContainerConfig instance if successful, otherwise None
    """

    # build path
    file_path = os.path.join(folder_path, config_filename)

    # read in config
    return ContainerConfig.load(file_path)
