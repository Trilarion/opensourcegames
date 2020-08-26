"""
Paths, properties.
"""

import os
import configparser

# paths
root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
entries_path = os.path.join(root_path, 'entries')
tocs_path = os.path.join(entries_path, 'tocs')
code_path = os.path.join(root_path, 'code')

local_config_file = os.path.join(root_path, 'local-config.ini')

config = configparser.ConfigParser()
config.read(local_config_file)


def get_config(key):
    """

    :param key:
    :return:
    """
    return config['general'][key]
