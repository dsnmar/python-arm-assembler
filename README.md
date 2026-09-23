# python-arm-assembler

Assembler for ARM assembly language.

An assembler is a program that translates assembly code into machine code (binary). 
Given an ARM assembly input, this assembler generates a raw binary file and a custom relocatable object file.
```
MOV R0, #5   # assembly
E3A00005     # binary (hex)
```
This project implements a simple ARM assembler written in Python.
It supports a subset of ARM instructions including:

- Data processing instructions (ADD, SUB, MOV, CMP, TST, etc.)
- Branch instructions (B, BL)
- Load/store instructions (LDR, STR)
- Multiply instruction (MUL)

The assembler performs two passes:

- First pass: builds a symbol table (labels → addresses)
- Second pass: encodes instructions into 32-bit machine code and generates relocation entries for unresolved branch symbols

## Features

- Label support (including labels on the same line as instructions)
- Immediate and register operands
- Basic memory addressing: [Rn] and [Rn, #imm]
- Binary output in little-endian format
- Custom `PYARMOBJ1` object file generation
- Symbol table generation
- ARM branch relocation support for B and BL
- Error handling for invalid syntax and operands

## Notes

- Only a subset of ARM instructions is supported
- Only condition AL is implemented
- Immediate encoding is simplified
- `.bin` output is raw machine code (not an executable ELF)
- `.obj` uses the custom `PYARMOBJ1` format, not ELF or COFF

## How to run ?
```
python assembler.py input.asm --output output.bin
```
The assembler always generates a corresponding `.obj` file containing machine code, symbols and relocation information. A `.bin` file is generated only when no unresolved relocations remain.
