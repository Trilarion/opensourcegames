"""
Paths, properties.
"""

import os

# paths
root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
games_path = os.path.join(root_path, 'games')
tocs_path = os.path.join(games_path, 'tocs')

local_properties_file = os.path.join(root_path, 'local.properties')