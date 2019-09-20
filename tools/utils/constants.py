"""
Paths, properties.
"""

import os

# paths
root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
entries_path = os.path.join(root_path, 'entries')
tocs_path = os.path.join(entries_path, 'tocs')

local_properties_file = os.path.join(root_path, 'local.properties')