import os
from pprint import pformat

from .call_slang import call_slang
from .call_sv_parser import call_sv_parser
from .util import is_single_file

def resolve_tool(tool=None):
    if tool is None:
        tool = os.environ.get('PSVINST_DEFAULT_TOOL', 'sv-parser')
    return tool

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
    def __init__(self, name, inst_name=None):
        super().__init__(name=name)
        self.inst_name = inst_name

    def __str__(self):
        if self.inst_name is not None:
            return f'{self.__class__.__name__}("{self.name}", "{self.inst_name}")'
        else:
            return f'{self.__class__.__name__}("{self.name}")'

    def __eq__(self, other):
        if self.inst_name is not None:
            return super().__eq__(other) and (self.inst_name == other.inst_name)
        else:
            return super().__eq__(other)

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

def get_defs(files, includes=None, defines=None, ignore_include=False, separate=False,
             ignore_errors=False, suppress_output=False, tool=None):

    single = is_single_file(files)

    tool = resolve_tool(tool)
    if tool == 'slang':
        out = call_slang(files=files, includes=includes, defines=defines,
                         ignore_include=ignore_include, separate=separate, full_tree=False,
                         ignore_errors=ignore_errors, suppress_output=suppress_output)
    elif tool == 'sv-parser':
        out = call_sv_parser(files=files, includes=includes, defines=defines,
                             ignore_include=ignore_include, separate=separate, full_tree=False)
    else:
        raise Exception(f'Unknown tool: {tool}')

    retval = [process_defs(elem['defs']) for elem in out['files']]

    if single:
        if len(retval) > 0:
            return retval[0]
        else:
            return []
    else:
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

def process_svinst_syntax_tree(result):
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
                    process_svinst_syntax_tree(items[0][1])
                )
            )
    return retval

def get_syntax_tree(files, includes=None, defines=None, ignore_include=False,
                    separate=False, ignore_errors=False, suppress_output=False,
                    tool=None):
    single = is_single_file(files)

    tool = resolve_tool(tool)

    if tool == 'slang':
        out = call_slang(files=files, includes=includes, defines=defines,
                         ignore_include=ignore_include, ignore_errors=ignore_errors,
                         separate=separate, suppress_output=suppress_output,
                         full_tree=True)
        return out
    elif tool == 'sv-parser':
        out = call_sv_parser(files=files, includes=includes, defines=defines,
                             ignore_include=ignore_include, separate=separate, full_tree=True)

        retval = [process_svinst_syntax_tree(elem['syntax_tree'])
                  for elem in out['files']]
        if single:
            if len(retval) > 0:
                return retval[0]
            else:
                return []
        else:
            return retval
    else:
        raise Exception(f'Unknown tool: {tool}')
