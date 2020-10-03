import pytest
from pathlib import Path
from svinst import *
from svinst.defchk import (ModInst, PkgInst)

VLOG_DIR = Path(__file__).resolve().parent / 'verilog'
TOOLS = ['slang']

@pytest.mark.parametrize('tool', TOOLS)
def test_test(tool):
    result = get_defs(VLOG_DIR / 'test.sv', tool=tool)
    assert result[0].insts == [ModInst("X"), ModInst("Y")]

@pytest.mark.parametrize('tool', TOOLS)
def test_broken(tool):
    with pytest.raises(Exception):
        get_defs(VLOG_DIR / 'broken.sv', tool=tool)

@pytest.mark.parametrize('tool', TOOLS)
def test_inc(tool):
    result = get_defs(VLOG_DIR / 'inc_test.sv', includes=[VLOG_DIR], tool=tool)
    assert result[0].insts == [ModInst("mod_name_from_inc_sv")]

@pytest.mark.parametrize('tool', TOOLS)
def test_def(tool):
    defines = {'MODULE_NAME': 'module_name_from_define', 'EXTRA_INSTANCE': None}
    result = get_defs(VLOG_DIR / 'def_test.sv', defines=defines, tool=tool)
    assert result[0].insts == [
        ModInst('module_name_from_define'),
        ModInst('module_from_ifdef')
    ]

@pytest.mark.parametrize('tool', TOOLS)
def test_simple(tool):
    get_syntax_tree(VLOG_DIR / 'simple.sv', tool=tool)

@pytest.mark.parametrize('tool', TOOLS)
def test_gen_test(tool):
    get_syntax_tree(VLOG_DIR / 'gen_test.sv', tool=tool)

@pytest.mark.parametrize('tool', TOOLS)
def test_pkg(tool):
    result = get_defs(VLOG_DIR / 'pkg.sv', tool=tool)
    assert result[0].insts == [
        PkgInst("b"),
        PkgInst("c"),
        PkgInst("f"),
        PkgInst("g")
    ]

@pytest.mark.parametrize('tool', TOOLS)
def test_intf(tool):
    result = get_defs(VLOG_DIR / 'intf.sv', tool=tool)
    assert result == []

@pytest.mark.parametrize('tool', TOOLS)
def test_intf2(tool):
    result = get_defs(VLOG_DIR / 'intf2.sv', tool=tool)
    assert result[0].insts == [ModInst('b')]

@pytest.mark.parametrize('tool', TOOLS)
def test_empty(tool):
    result = get_defs(VLOG_DIR / 'empty.sv', tool=tool)
    assert result == []

@pytest.mark.parametrize('tool', TOOLS)
def test_multi(tool):
    result = get_defs([
        VLOG_DIR / 'multi' / 'define1.v',
        VLOG_DIR / 'multi' / 'test1.sv',
        VLOG_DIR / 'multi' / 'define2.v',
        VLOG_DIR / 'multi' / 'dut.v',
    ], tool=tool)
    assert result == []
