"""
Where no requirements.txt or setup.py or other information is given, get an idea of the external dependencies
by parsing the Python files and looking for import statements.
"""

import re
from utils.utils import *


def local_module(module_base, file_path, module):
    """

    """
    module = module.split('.')
    module[-1] += '.py'
    pathA = os.path.join(module_base, *module)
    pathB = os.path.join(file_path, *module)
    return os.path.exists(pathA) or os.path.exists(pathB)

if __name__ == "__main__":

    system_libraries = {'__builtin__', '.', '..', '*', 'array', 'os', 'copy', 'codecs', 'collections', 'cPickle', 'datetime', 'decimal', 'email',
        'io', 'math', 'md5', 'operator', 'random', 're', 'sha', 'shutil', 'smtplib', 'socket', 'string', 'struct', 'subprocess',
        'sys', 'thread', 'threading', 'time', 'traceback', 'types', 'urllib', 'urllib2', 'yaml', 'yaml3', 'zlib'}
    regex_import = re.compile(r"^\s*import (.*)", re.MULTILINE)
    regex_from = re.compile(r"^\s*from (.*) import (.*)", re.MULTILINE)
    regex_comment = re.compile(r"(#.*)$", re.MULTILINE)
    regex_as = re.compile(r"(as.*)$", re.MULTILINE)

    # modify these locations
    root_folder = r''
    module_base = r''

    # get all *.py files below the root_folder
    files = []
    for dirpath, dirnames, filenames in os.walk(root_folder):
        filenames = [x for x in filenames if x.endswith('.py') or x.endswith('.pyw')]
        if filenames:
            filenames = [os.path.join(dirpath, x) for x in filenames]
            files.extend(filenames)
    print('found {} files'.format(len(files)))

    # iterate over all these files
    imports = []
    for file in files:

        # get file path
        file_path = os.path.split(file)[0]

        # read file content
        content = read_text(file)

        # remove comments
        content = regex_comment.sub('', content)

        # remove as clauses
        content = regex_as.sub('', content)

        # search for "import .." statements
        matches = regex_import.findall(content)

        for match in matches:
            modules = match.split(',') # split if more
            for module in modules:
                module = module.strip()
                if not local_module(module_base, file_path, module):
                    imports.append(module)

        # search for "from .. import .." statements
        matches = regex_from.findall(content)

        for match in matches:
            module = match[0] # only the from part
            module = module.strip()
            if not local_module(module_base, file_path, module):
                imports.append(module)

    # throw out duplicates
    imports = list(set(imports) - system_libraries)

    # sort
    imports.sort()

    # display
    print('\n'.join(imports))
