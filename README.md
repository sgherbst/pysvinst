# pysvinst

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Actions Status](https://github.com/sgherbst/pysvinst/workflows/Regression/badge.svg)](https://github.com/sgherbst/pysvinst/actions)
[![codecov](https://codecov.io/gh/sgherbst/pysvinst/branch/master/graph/badge.svg)](https://codecov.io/gh/sgherbst/pysvinst)

This Python library examines SystemVerilog files to determine what modules are defined and what modules are instantiated.  The backend uses [sv-parser](https://github.com/dalance/sv-parser), which has good support of SystemVerilog 2017.

## Purpose

The Verilog language has contains features for defining configs and libraries.  However, these features are not well-supported by open-source tools, and even some commercial synthesis tools.  By extracting a list of modules defined and instantiated in a file, a user can work around this problem by constructing their own design hierarchy outside of Verilog, and then passing that list of files back into the simulator / synthesis tool.

## Installation

This package can be installed via pip:
```shell
> pip install svinst
```

Alternatively, you can clone the repository and build the package yourself.  This requires that [Rust](https://www.rust-lang.org/tools/install) is installed.
```shell
> git clone https://github.com/sgherbst/pysvinst.git
> cd pysvinst
> pip install -e .
```

## Usage

The main functionality of this package is provided through the function ``get_mod_defs``.  In this first example, a list of module definitions is returned, each one containing a list module instantiations (if any) contained in that module definition.  

```python
>>> from svinst import get_mod_defs
>>> defs = get_mod_defs('tests/verilog/test.sv')
>>> _ = [print(str(def_)) for def_ in defs]
ModDef("A", [
])
ModDef("B", [
])
ModDef("C", [
  ModInst("A", "I0"),
  ModInst("B", "I1")
])
ModDef("D", [
  ModInst("X", "I0"),
  ModInst("Y", "I1")
])
```

It is also possible to add define variables and include directory paths, since both of these can change the modules that get defined and instantiated:

```python
>>> get_mod_defs('tests/verilog/inc_test.sv', includes=['tests/verilog'])
>>> get_mod_defs('tests/verilog/def_test.sv',
                 defines={'MODULE_NAME': 'module_name_from_define', 'EXTRA_INSTANCE': None})
```

If there is a syntax error, an error message is printed and an Exception is raised.

```python
>>> get_mod_defs('tests/verilog/broken.sv')
parse failed: "tests/verilog/broken.sv"
 tests/verilog/broken.sv:5:10
  |
5 | endmodule
  |  
```

Finally, the user can get a full syntax tree for advanced processing, using the command ``get_syntax_tree``.  That command also allows the arguments ``includes`` and ``defines``.

```python
>>> from svinst import get_syntax_tree
>>> tree = get_syntax_tree('tests/verilog/simple.sv')
>>> _ = [print(elem) for elem in tree]
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
```
