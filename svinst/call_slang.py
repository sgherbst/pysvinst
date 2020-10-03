import subprocess
import json
from pathlib import Path

from .util import is_single_file

def call_slang(files, includes=None, defines=None, ignore_include=False,
               full_tree=False, separate=False):
    # set defaults
    if includes is None:
        includes = []
    if defines is None:
        defines = {}

    # wrap files if needed
    if is_single_file(files):
        files = [files]

    # prepare arguments
    args = [Path(__file__).resolve().parent / 'bin' / 'slang']
    args += files
    for k, v in defines.items():
        if v is not None:
            args += ['-D', f'{k}={v}']
        else:
            args += ['-D', f'{k}']
    for elem in includes:
        args += ['-I', f'{elem}']
    if ignore_include:
        # TODO: implement
        pass
    if full_tree:
        args += ['--ast-json', '-']
    if not separate:
        args += ['--single-unit']

    # convert arguments to strings
    args = [str(elem) for elem in args]

    # call command
    result = subprocess.run(args, capture_output=True, encoding='utf-8')
    returncode, stdout, stderr = result.returncode, result.stdout, result.stderr

    # return result
    if full_tree:
        return parse_full_tree(returncode=returncode, stdout=stdout, stderr=stderr)
    else:
        return parse_modules(returncode=returncode, stdout=stdout, stderr=stderr)


def parse_modules(returncode, stdout, stderr):
    error_indicator = 'error:'
    unknown_module = 'error: unknown module'
    unknown_package = 'error: unknown package'
    unknown_interface = 'error: unknown interface'

    files = {}

    print_error = False
    found_error = False
    instance_type = None

    for line in stdout.splitlines():
        if error_indicator in line:
            if unknown_module in line:
                lidx = line.index(unknown_module)
                ridx = lidx + len(unknown_module)
                instance_type = 'module'
                print_error = False
            elif unknown_package in line:
                lidx = line.index(unknown_package)
                ridx = lidx + len(unknown_package)
                instance_type = 'package'
                print_error = False
            elif unknown_interface in line:
                lidx = line.index(unknown_interface)
                ridx = lidx + len(unknown_interface)
                instance_type = 'interface'
                print_error = False
            else:
                print(line)
                print_error = True
                found_error = True
                continue
        else:
            if print_error:
                print(line)
            continue

        # parse out file name, line character
        left = line[:lidx].strip()
        file_info = left.split(':')
        file_name = ':'.join(file_info[:-3])
        file_line = file_info[-3]
        file_char = file_info[-2]

        # parse out the module name
        right = line[ridx:].strip()
        name = right[1:-1]

        # add a new entry for this file if needed
        if file_name not in files:
            files[file_name] = {}

        # add module name (use a dictionary rather than
        # a set, so as to keep the original order)
        files[file_name][name] = instance_type

    # raise an exception at this point if there was an error
    if found_error:
        raise Exception('slang detected syntax error(s)')

    # build structure as needed for output
    retval = {'files': []}
    for file_name, modules in files.items():
        file_dict = {}
        file_dict['file_name'] = file_name
        file_dict['defs'] = []
        def_dict = {}
        file_dict['defs'].append(def_dict)
        def_dict['mod_name'] = Path(file_name).stem
        insts = []
        def_dict['insts'] = insts
        for name, instance_type in modules.items():
            if instance_type == 'module':
                inst = {'mod_name': name, 'inst_name': None}
            elif instance_type == 'package':
                inst = {'pkg_name': name}
            elif instance_type == 'interface':
                # for consistency with sv-parser, interface instances
                # are treated like modules
                inst = {'mod_name': name, 'inst_name': None}
            else:
                raise Exception(f'Unknown instance type: {instance_type}.')
            insts.append(inst)
        retval['files'].append(file_dict)

    return retval

def parse_full_tree(returncode, stdout, stderr):
    result = json.loads(stdout)
    return result
