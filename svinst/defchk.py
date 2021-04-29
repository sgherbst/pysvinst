from pathlib import Path
from pprint import pformat
import subprocess
import yaml
import sys

def error_text(s):
    return f'**{s}**'

class SVInstParsingError(Exception):
    """Exception raised for errors while parsing.

    Attributes:
        error_set: Set of file indices that have parsing errors (starts at zero)
        file_list: List of files that were passed to svinst
        svinst_stderr: Output of the svinst tool to standard error (stderr)
        svinst_retcode: Return code of svinst
    """

    def __init__(self, error_set=None, file_list=None, svinst_stderr=None,
                 svinst_retcode=None, nl='\n'):
        # save information
        self.error_set = error_set
        self.file_list = file_list
        self.svinst_stderr = svinst_stderr
        self.svinst_retcode = svinst_retcode

        # render message
        message = []
        if svinst_stderr is not None:
            message += [f'{svinst_stderr}']
        if (error_set is not None) and (file_list is not None):
            # render a list of indices
            # make a list of the file indices with errors, starting
            # at "1" to make it more human-readable
            indices = list(error_set)
            indices = sorted(indices)
            indices = [str(x+1) for x in indices]
            indices = ', '.join(indices)

            # mark the files with errors
            files_str = []
            for k, file in enumerate(file_list):
                name = Path(file).name
                if k in error_set:
                    name = error_text(name)
                files_str.append(name)
            marked_list = '[' + ', '.join(files_str) + ']'

            # create the error message
            message += [f'Error in file(s) {indices}: {marked_list}']
        if svinst_retcode is not None:
            message += [f'svinst returned code {svinst_retcode}.']

        super().__init__(nl.join(message))

def is_single_file(files):
    return isinstance(files, (str, Path))

def find_error_indices(files, stdout):
    # try to parse the YAML output
    d = yaml.safe_load(stdout)

    # figure out which files had errors (i.e., which are missing)
    error_set = set()
    idx = 0
    for k in range(len(files)):
        if (idx < len(d['files']) and
            (str(d['files'][idx]['file_name']) == str(files[k]))):
            idx += 1
        else:
            error_set.add(k)

    # return the indices
    return error_set

def call_svinst(files, includes=None, defines=None, ignore_include=False, full_tree=False,
                separate=False, show_macro_defs=False, explain_error=True):
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
    if separate:
        args += ['--separate']
    if show_macro_defs:
        args += ['--show-macro-defs']

    # convert arguments to strings
    args = [str(elem) for elem in args]

    # call command
    result = subprocess.run(args, capture_output=True, encoding='utf-8')
    if result.returncode != 0:
        # find indices of files with errors, if desired
        error_set = None
        if explain_error and (len(files) > 1):
            try:
                error_set = find_error_indices(files=files, stdout=result.stdout)
            except:
                pass

        # raise an exception
        raise SVInstParsingError(error_set=error_set,file_list=files,
                                 svinst_stderr=result.stderr, svinst_retcode=result.returncode)

    # parse output as YAML
    return yaml.safe_load(result.stdout)

class Def:
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

class MacroDef:
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return f"{self.__class__.__name__}('{self.text}')"

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                (self.text == other.text))

class ModDef(Def):
    pass

class PkgDef(Def):
    pass

class IntfDef(Def):
    pass

class Inst:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'{self.__class__.__name__}("{self.name}")'

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                (self.name == other.name))

class ModInst(Inst):
    def __init__(self, name, inst_name):
        super().__init__(name=name)
        self.inst_name = inst_name

    def __str__(self):
        return f'{self.__class__.__name__}("{self.name}", "{self.inst_name}")'

    def __eq__(self, other):
        return super().__eq__(other) and (self.inst_name == other.inst_name)

class PkgInst(Inst):
    pass

def process_defs(result):
    retval = []

    if result is None:
        result = []

    for entry in result:
        if 'pkg_name' in entry:
            def_ = PkgDef(name=entry['pkg_name'])
        elif 'intf_name' in entry:
            def_ = IntfDef(name=entry['intf_name'])
        elif 'mod_name' in entry:
            def_ = ModDef(name=entry['mod_name'])
        else:
            raise Exception(f'Unknown definition: {entry}')

        if entry.get('insts', None) is not None:
            for inst in entry['insts']:
                if 'mod_name' in inst:
                    def_.insts.append(ModInst(inst['mod_name'], inst['inst_name']))
                elif 'pkg_name' in inst:
                    def_.insts.append(PkgInst(inst['pkg_name']))
                else:
                    raise Exception(f'Unknown instance: {inst}')

        retval.append(def_)

    return retval

def process_macro_defs(result):
    retval = []

    if result is None:
        result = []

    for entry in result:
        retval.append(MacroDef(text=entry))

    return retval

def get_defs(files, includes=None, defines=None, ignore_include=False,
             separate=False, show_macro_defs=False, explain_error=True):
    single = is_single_file(files)

    out = call_svinst(files=files, includes=includes, defines=defines,
                      ignore_include=ignore_include, separate=separate,
                      show_macro_defs=show_macro_defs, explain_error=explain_error,
                      full_tree=False)

    retval = []
    for elem in out['files']:
        retval.append([])
        retval[-1].extend(process_defs(elem['defs']))
        if show_macro_defs:
            macro_defs = process_macro_defs(elem['macro_defs'])
            macro_defs = sorted(macro_defs, key=lambda x: x.text)
            retval[-1].extend(macro_defs)

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
    # just return an empty list of result is None
    if result is None:
        return []

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

def get_syntax_tree(files, includes=None, defines=None, ignore_include=False,
                    separate=False, show_macro_defs=False, explain_error=True):
    single = is_single_file(files)

    out = call_svinst(files=files, includes=includes, defines=defines,
                      ignore_include=ignore_include, separate=separate,
                      show_macro_defs=show_macro_defs, explain_error=explain_error,
                      full_tree=True)
    retval = [process_syntax_tree(elem['syntax_tree']) for elem in out['files']]

    if single:
        retval = retval[0]

    return retval
