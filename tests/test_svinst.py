import pytest
from pathlib import Path
from svinst import *
from svinst.defchk import (ModDef, ModInst, SyntaxNode, SyntaxToken,
                           PkgDef, PkgInst, IntfDef, MacroDef)

VLOG_DIR = Path(__file__).resolve().parent / 'verilog'

def test_test():
    result = get_defs(VLOG_DIR / 'test.sv')
    expct = [
      ModDef("A", [
      ]),
      ModDef("B", [
      ]),
      ModDef("C", [
        ModInst("A", "I0"),
        ModInst("B", "I1")
      ]),
      ModDef("D", [
        ModInst("X", "I0"),
        ModInst("Y", "I1")
      ])
    ]
    assert result == expct

def test_broken(capsys):
    # determine the path to the broken file
    broken_file = VLOG_DIR / 'broken.sv'

    # expect parsing of these files to fail
    with pytest.raises(Exception):
        get_defs(broken_file)

    # make sure the error message includes the right information
    _, err = capsys.readouterr()
    lines = err.splitlines()
    assert lines[0].strip() == f'parse failed: "{broken_file}"'

def test_inc():
    result = get_defs(VLOG_DIR / 'inc_test.sv', includes=[VLOG_DIR])
    expct = [
      ModDef("inc_top", [
          ModInst("mod_name_from_inc_sv", "I0")
      ])
    ]
    assert result == expct

def test_def():
    defines = {'MODULE_NAME': 'module_name_from_define', 'EXTRA_INSTANCE': None}
    result = get_defs(VLOG_DIR / 'def_test.sv', defines=defines, show_macro_defs=True)
    expct = [
      ModDef("def_top", [
        ModInst("module_name_from_define", "I0"),
        ModInst("module_from_ifdef", "I1")
      ]),
      MacroDef('Define { identifier: "EXTRA_INSTANCE", arguments: [], text: None }'),
      MacroDef('Define { identifier: "MODULE_NAME", arguments: [], text: Some(DefineText { text: "module_name_from_define", origin: None }) }')
    ]
    assert result == expct

def test_simple():
    result = get_syntax_tree(VLOG_DIR / 'simple.sv')
    expct = [
      SyntaxNode("SourceText", [
        SyntaxNode("Description", [
          SyntaxNode("ModuleDeclaration", [
            SyntaxNode("ModuleDeclarationAnsi", [
              SyntaxNode("ModuleAnsiHeader", [
                SyntaxNode("ModuleKeyword", [
                  SyntaxNode("Keyword", [
                    SyntaxToken("module", line=1)
                  ])
                ]),
                SyntaxNode("ModuleIdentifier", [
                  SyntaxNode("Identifier", [
                    SyntaxNode("SimpleIdentifier", [
                      SyntaxToken("A", line=1)
                    ])
                  ])
                ]),
                SyntaxNode("Symbol", [
                  SyntaxToken(";", line=1)
                ])
              ]),
              SyntaxNode("Keyword", [
                SyntaxToken("endmodule", line=2)
              ])
            ])
          ])
        ])
      ])
    ]
    assert result == expct

def test_pkg():
    result = get_defs(VLOG_DIR / 'pkg.sv')
    expct = [
        PkgDef("i"),
        ModDef("A", [
            PkgInst("b")
        ]),
        PkgDef("j"),
        ModDef("B", [
            PkgInst("c")
        ]),
        ModDef("E", [
            PkgInst("f"),
            PkgInst("g")
        ]),
        PkgDef("k")
    ]
    assert result == expct

def test_intf():
    result = get_defs(VLOG_DIR / 'intf.sv')
    expct = [
        IntfDef("b"),
        ModDef("A", [
        ]),
        IntfDef("c"),
        ModDef("E", [
          ModInst("c", "c_i"),
        ]),
        IntfDef("d")
    ]
    assert result == expct

def test_empty():
    result = get_defs(VLOG_DIR / 'empty.sv')
    expct = []
    assert result == expct

def test_multi():
    result = get_defs([
        VLOG_DIR / 'multi' / 'define1.v',
        VLOG_DIR / 'multi' / 'test1.sv',
        VLOG_DIR / 'multi' / 'define2.v',
        VLOG_DIR / 'multi' / 'dut.v'
    ])
    expct = [
        [],
        [ModDef("test", [ModInst("dut", "u0")])],
        [],
        [ModDef("dut")]
    ]
    assert result == expct

def test_mux():
    result = get_defs([
        VLOG_DIR / 'mux' / 'mux1_define.svh',
        VLOG_DIR / 'mux' / 'mux.sv',
        VLOG_DIR / 'mux' / 'mux1_undef.svh',
        VLOG_DIR / 'mux' / 'mux2_define.svh',
        VLOG_DIR / 'mux' / 'mux.sv',
        VLOG_DIR / 'mux' / 'mux2_undef.svh'
    ])
    expct = [
        [],
        [ModDef('mux1')],
        [],
        [],
        [ModDef('mux2')],
        []
    ]
    assert result == expct

def test_error_explain(capsys):
    # expect parsing of these files to fail
    with pytest.raises(Exception):
        get_defs([
            VLOG_DIR / 'mux' / 'mux.sv',
            VLOG_DIR / 'mux' / 'mux1_undef.svh',
            VLOG_DIR / 'mux' / 'mux2_define.svh',
            VLOG_DIR / 'broken.sv',
            VLOG_DIR / 'mux' / 'mux.sv',
            VLOG_DIR / 'mux' / 'mux2_undef.svh',
            VLOG_DIR / 'mux' / 'mux.sv'
        ])

    # make sure the error message includes the right information
    _, err = capsys.readouterr()
    lines = err.splitlines()
    assert lines[-1].startswith('Error in file(s) 1, 4, 7:')
