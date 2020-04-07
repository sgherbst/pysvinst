from pathlib import Path
from pprint import pformat
import subprocess
import yaml
import sys

def is_single_file(files):
    return isinstance(files, (str, Path))

def call_svinst(files, includes=None, defines=None, ignore_include=False, full_tree=False):
    # set defaults
    if includes is None:
        includes = []
    if defines is None:
        defines = {}

    # wrap files if needed
    if is_single_file(files):
        files = [files]

    # prepare arguments
    args = [Path(__file__).resolve().parent / 'bin' / 'svinst']
    args += files
    for k, v in defines.items():
        if v is not None:
            args += ['-d', f'{k}={v}']
        else:
            args += ['-d', f'{k}']
    for elem in includes:
        args += ['-i', f'{elem}']
    if ignore_include:
        args += ['--ignore-include']
    if full_tree:
        args += ['--full-tree']

    # convert arguments to strings
    args = [str(elem) for elem in args]

    # call command
    result = subprocess.run(args, capture_output=True, encoding='utf-8')
    if result.returncode != 0:
        print(f'{result.stderr}', file=sys.stderr)
        raise Exception(f'svinst returned code {result.returncode}.')

    # parse output as YAML
    return yaml.safe_load(result.stdout)

class ModDef:
    def __init__(self, name, insts=None):
        # set defaults
        if insts is None:
            insts = []

        # save settings
        self.name = name
        self.insts = insts

    def __str__(self, tab_str='  ', nl='\n'):
        retval = ''
        retval += f'{self.__class__.__name__}("{self.name}", ['
        retval += f','.join([f'{nl}{tab_str}{inst}' for inst in self.insts])
        retval += f'{nl}])'

        return retval

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                (self.name == other.name) and
                (len(self.insts) == len(other.insts)) and
                all(self_inst == other_inst for self_inst, other_inst in zip(self.insts, other.insts)))

class ModInst:
    def __init__(self, mod_name, inst_name):
        self.mod_name = mod_name
        self.inst_name = inst_name

    def __str__(self):
        return f'{self.__class__.__name__}("{self.mod_name}", "{self.inst_name}")'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                (self.mod_name == other.mod_name) and
                (self.inst_name == other.inst_name))

class PkgDef:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'{self.__class__.__name__}("{self.name}")'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (self.name == other.name)

class PkgInst:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'{self.__class__.__name__}("{self.name}")'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (self.name == other.name)

class IntfDef:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'{self.__class__.__name__}("{self.name}")'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (self.name == other.name)

def process_defs(result):
    retval = []

    for def_ in result:
        if 'pkg_name' in def_:
            retval.append(PkgDef(name=def_['pkg_name']))
        elif 'intf_name' in def_:
            retval.append(IntfDef(name=def_['intf_name']))
        elif 'mod_name' in def_:
            name = def_['mod_name']
            insts = []
            if 'insts' in def_ and def_['insts'] is not None:
                for inst in def_['insts']:
                    if 'mod_name' in inst:
                        insts.append(ModInst(inst['mod_name'], inst['inst_name']))
                    elif 'pkg_name' in inst:
                        insts.append(PkgInst(inst['pkg_name']))
                    else:
                        raise Exception(f'Unknown instance: {inst}')
            retval.append(ModDef(name, insts))
        else:
            raise Exception(f'Unknown definition: {def_}')

    return retval

def get_defs(files, includes=None, defines=None, ignore_include=False):
    single = is_single_file(files)

    out = call_svinst(files=files, includes=includes, defines=defines,
                      ignore_include=ignore_include, full_tree=False)

    retval = [process_defs(elem['defs']) for elem in out['files']]

    if single:
        retval = retval[0]

    return retval

class SyntaxToken:
    def __init__(self, token, line):
        self.token = token
        self.line = line

    def __str__(self):
        return f'{self.__class__.__name__}("{self.token}", line={self.line})'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                (self.token == other.token) and
                (self.line == other.line))

class SyntaxNode:
    def __init__(self, name, children=None):
        # set defaults
        if children is None:
            children = []

        # save settings
        self.name = name
        self.children = children

    def __str__(self, tab_str='  ', tab_cnt=0, nl='\n'):
        inst_strs = []
        for inst in self.children:
            if isinstance(inst, SyntaxToken):
                inst_strs.append((tab_cnt+1)*tab_str + inst.__str__())
            else:
                inst_strs.append(inst.__str__(tab_str, tab_cnt+1, nl))

        retval = ''
        retval += f'{tab_cnt*tab_str}{self.__class__.__name__}("{self.name}", ['
        retval += f','.join([f'{nl}{elem}' for elem in inst_strs])
        retval += f'{nl}{tab_cnt*tab_str}])'

        return retval

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                (self.name == other.name) and
                (len(self.children) == len(other.children)) and
                all(self_child == other_child for self_child, other_child in zip(self.children, other.children)))

def is_token(d):
    return d.keys() == {'Token', 'Line'}

def process_syntax_tree(result):
    retval = []
    for elem in result:
        if is_token(elem):
            retval.append(SyntaxToken(elem['Token'], elem['Line']))
        else:
            items = list(elem.items())
            if len(items) != 1:
                err_str = ''
                err_str += f'Expected dictionary of length 1, found:\n'
                err_str += pformat(elem, indent=2)
                raise Exception(err_str)
            retval.append(
                SyntaxNode(
                    items[0][0],
                    process_syntax_tree(items[0][1])
                )
            )
    return retval

def get_syntax_tree(files, includes=None, defines=None, ignore_include=False):
    single = is_single_file(files)

    out = call_svinst(files=files, includes=includes, defines=defines,
                      ignore_include=ignore_include, full_tree=True)

    retval = [process_syntax_tree(elem['syntax_tree']) for elem in out['files']]

    if single:
        retval = retval[0]

    return retval
