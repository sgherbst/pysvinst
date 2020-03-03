import pytest
from pathlib import Path
from svinst import *
from svinst.modchk import ModDef, ModInst, SyntaxNode, SyntaxToken

VLOG_DIR = Path(__file__).resolve().parent / 'verilog'

def test_test():
    result = get_mod_defs(VLOG_DIR / 'test.sv')
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

def test_broken():
    with pytest.raises(Exception):
        get_mod_defs(VLOG_DIR / 'broken.sv')

def test_inc():
    result = get_mod_defs(VLOG_DIR / 'inc_test.sv', includes=[VLOG_DIR])
    expct = [
      ModDef("inc_top", [
          ModInst("mod_name_from_inc_sv", "I0")
      ])
    ]
    assert result == expct

def test_def():
    defines = {'MODULE_NAME': 'module_name_from_define', 'EXTRA_INSTANCE': None}
    result = get_mod_defs(VLOG_DIR / 'def_test.sv', defines=defines)
    expct = [
      ModDef("def_top", [
        ModInst("module_name_from_define", "I0"),
        ModInst("module_from_ifdef", "I1")
      ])
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