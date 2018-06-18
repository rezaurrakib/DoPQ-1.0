#!/usr/bin/env python
# encoding: utf-8
"""
log.py

Provides logging support
"""
import logging


LOGGER_NAME = "DOPQ"


def get_module_log(module_name):
    """
    Returns the specific log for a module.

    :param module_name: Module name to use.
    :return: Log object
    """
    return logging.getLogger("{}.{}".format(LOGGER_NAME, module_name))


def init_log(file_name='dopq.log', log_level=logging.DEBUG, file_log_level=logging.DEBUG):
    """
    Initializes a log object

    :param file_name: Path to logfile.
    :param log_level: Level to use for output.
    :param file_log_level: Level to use for file logging.
    :return: Logger object
    """

    # create new logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(min([log_level, file_log_level]))

    # set format string
    format_string = '%(levelname)s in %(name)s: %(message)s'
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(format_string, datefmt="%d.%m.%Y-%H:%M:%S"))
    handler.setLevel(log_level)
    logger.addHandler(handler)

    format_string = '%(asctime)s %(levelname)s in %(name)s: %(message)s'
    file_handler = logging.FileHandler(file_name)
    file_handler.setFormatter(logging.Formatter(format_string, datefmt="%d.%m.%Y-%H:%M:%S"))
    file_handler.setLevel(file_log_level)
    logger.addHandler(file_handler)

    return logger
