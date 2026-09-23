import argparse
import json
from tables import *

def read_file(path):
    tokens_lines = []
    with open(path) as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            raw_line = raw_line.split(";")[0]
            raw_line = raw_line.upper()
            if not raw_line:
                continue
            tokens = raw_line.replace(",", "").replace("[", " [ ").replace("]", " ] ").split()
            tokens_lines.append(tokens)
    return tokens_lines

def is_label(tokens):
    if tokens != [] and tokens[0].endswith(":"):
        return True
    else:
        return False

def get_label_name(tokens):
    if is_label(tokens):
        label = tokens[0][:-1]
        return label
    else:
        return None

def first_pass(tokens_lines):
    symbol_table = {}
    address = 0
    for tokens_line in tokens_lines:
        if not tokens_line:
            continue
        idx = 0
        if is_label(tokens_line):
            label = get_label_name(tokens_line).upper()
            if label in symbol_table:
                raise Exception(f"Duplicate label: {label}")
            symbol_table[label] = address
            idx = 1
        if idx < len(tokens_line):
            address += 4
    return symbol_table

def parse_instruction(tokens_lines):
    instructions = []
    for tokens_line in tokens_lines:
        if not tokens_line:
            continue
        idx = 0
        if is_label(tokens_line):
            idx = 1
        if idx >= len(tokens_line):
            continue
        mnemonic = tokens_line[idx]
        if mnemonic not in INSTRUCTION_SET:
            raise Exception(f"Unknown instruction: {mnemonic}")
        instruction = {}
        instruction["mnemonic"] = mnemonic
        instruction["class"] = INSTRUCTION_SET[mnemonic]["class"]
        if "opcode" in INSTRUCTION_SET[mnemonic]:
            instruction["opcode"] = INSTRUCTION_SET[mnemonic]["opcode"]
        instruction["operands"] = tokens_line[idx + 1:]
        instructions.append(instruction)
    return instructions

def encode_data_processing(instruction):
    mnemonic = instruction["mnemonic"]
    ops = instruction["operands"]
    if ops[-1].startswith("#"):
        I = OPERAND_TYPE["IMMEDIATE"]
    else:
        I = OPERAND_TYPE["REGISTER"]
    if mnemonic in FLAG_ONLY_INSTRUCTIONS:
        S = 1
    else:
        S = 0
    if len(ops) == 3 and mnemonic in {"ADD", "SUB", "AND", "ORR", "EOR"}:
        Rd = ops[0]
        Rn = ops[1]
        Operand2 = ops[2]
    elif len(ops) == 2 and mnemonic in {"MOV", "MVN"}:
        Rd = ops[0]
        Rn = 0
        Operand2 = ops[1]
    elif len(ops) == 2 and mnemonic in {"CMP", "TST"}:
        Rd = 0
        Rn = ops[0]
        Operand2 = ops[1]
    else:
        raise Exception(f"Invalid syntax for {mnemonic}: {ops}")
    if Rd != 0:
        if Rd not in REGISTERS:
            raise Exception(f"Invalid destination register {Rd} in {mnemonic}")
        Rd = REGISTERS[Rd]
    if Rn != 0:
        if Rn not in REGISTERS:
            raise Exception(f"Invalid source register {Rn} in {mnemonic}")
        Rn = REGISTERS[Rn]
    if Operand2.startswith("#"):
        try:
            Operand2 = int(Operand2[1:])
        except ValueError:
            raise Exception(f"Invalid immediate {Operand2} in {mnemonic}")
        if Operand2 < 0 or Operand2 > 0xFFF:
            raise Exception(f"Immediate out of range (0-4095) in {mnemonic}: {Operand2}")
    else:
        if Operand2 not in REGISTERS:
            raise Exception(f"Invalid operand {Operand2} in {mnemonic}")
        Operand2 = REGISTERS[Operand2]
    Cond = CONDITIONS["AL"]
    Opcode = instruction["opcode"]
    word = 0
    word |= Cond << 28
    word |= I << 25
    word |= Opcode << 21
    word |= S << 20
    word |= Rn << 16
    word |= Rd << 12
    word |= Operand2
    return word

def encode_branch(instruction, symbol_table, address):
    if len(instruction["operands"]) != 1:
        raise Exception(f"{instruction['mnemonic']} expects exactly one label")
    label = instruction["operands"][0]
    if instruction["mnemonic"] == "BL":
        L = 1
    else:
        L = 0
    Cond = CONDITIONS["AL"]
    word = 0
    word |= Cond << 28
    word |= 0b101 << 25
    word |= L << 24
    if label in symbol_table:
        target = symbol_table[label]
        offset = (target - address - 8) >> 2
        word |= offset & 0xFFFFFF
        return word, None
    relocation = {
        "offset": address,
        "type": "ARM_BRANCH24",
        "symbol": label
    }
    return word, relocation

def encode_load_store(instruction):
    ops = instruction["operands"]
    if len(ops) not in (4, 5):
        raise Exception(f"{instruction['mnemonic']} expects Rd, [Rn] or Rd, [Rn, #imm], got {ops}")
    if ops[1] != "[" or ops[-1] != "]":
        raise Exception(f"Invalid memory syntax in {instruction['mnemonic']}: {ops}")
    Cond = CONDITIONS["AL"]
    I = 0
    P = 1
    U = 1
    B = 0
    W = 0
    L = LOAD_STORE_OPCODES[instruction["mnemonic"]]
    if ops[0] not in REGISTERS:
        raise Exception(f"Invalid destination register {ops[0]} in {instruction['mnemonic']}")
    if ops[2] not in REGISTERS:
        raise Exception(f"Invalid base register {ops[2]} in {instruction['mnemonic']}")
    Rd = REGISTERS[ops[0]]
    Rn = REGISTERS[ops[2]]
    if len(ops) == 5:
        if not ops[3].startswith("#"):
            raise Exception(f"Expected immediate offset in {instruction['mnemonic']}, got {ops[3]}")
        try:
            Offset = int(ops[3][1:])
        except ValueError:
            raise Exception(f"Invalid offset {ops[3]} in {instruction['mnemonic']}")
        if Offset < 0 or Offset > 0xFFF:
            raise Exception(f"Offset out of range (0-4095) in {instruction['mnemonic']}: {Offset}")
    else:
        Offset = 0
    word = 0
    word |= Cond << 28
    word |= 0b01 << 26
    word |= I << 25
    word |= P << 24
    word |= U << 23
    word |= B << 22
    word |= W << 21
    word |= L << 20
    word |= Rn << 16
    word |= Rd << 12
    word |= Offset & 0xFFF
    return word

def encode_multiply(instruction):
    if len(instruction["operands"]) != 3:
        raise Exception(f"MUL expects 3 operands, got {instruction['operands']}")
    for op in instruction["operands"]:
        if op not in REGISTERS:
            raise Exception(f"Invalid register {op} in MUL")
    Rd = REGISTERS[instruction["operands"][0]]
    Rn = 0
    Rm = REGISTERS[instruction["operands"][1]]
    Rs = REGISTERS[instruction["operands"][2]]
    Cond = CONDITIONS["AL"]
    A = 0
    S = 0
    word = 0
    word |= Cond << 28
    word |= A << 21
    word |= S << 20
    word |= Rd << 16
    word |= Rn << 12
    word |= Rs << 8
    word |= 0b1001 << 4
    word |= Rm << 0
    return word

def encode_instruction(instruction, symbol_table, address):
    relocation = None
    if instruction["class"] == "data_processing":
        word = encode_data_processing(instruction)
    elif instruction["class"] == "branch":
        return encode_branch(
            instruction,
            symbol_table,
            address
        )
    elif instruction["class"] == "load_store":
        word = encode_load_store(instruction)
    elif instruction["class"] == "multiply":
        word = encode_multiply(instruction)
    else:
        raise Exception(f"Unsupported instruction class: {instruction['class']}")
    return word, relocation

def second_pass(instructions, symbol_table):
    words = []
    relocations = []
    address = 0
    for instruction in instructions:
        word, relocation = encode_instruction(instruction, symbol_table, address)
        words.append(word)
        if relocation is not None:
            relocations.append(relocation)
        address += 4
    return words, relocations

def write_binary(words, output_path):
    with open(output_path, "wb") as f:
        for word in words:
            bytes_data = word.to_bytes(4, byteorder="little")
            f.write(bytes_data)
    return output_path

def write_object(words, symbol_table, relocations, obj_path):
    code = bytearray()
    for word in words:
        code.extend(word.to_bytes(4, byteorder="little"))
    obj_data = {
        "format": "PYARMOBJ1",
        "architecture": "ARM32",
        "endianness": "little",
        "code": code.hex(),
        "symbols": symbol_table,
        "relocations": relocations
    }
    with open(obj_path, "w") as f:
        json.dump(obj_data, f, indent=4)
    return obj_path

def assemble(input_path, output_path, obj_path):
    tokens = read_file(input_path)
    symbol_table = first_pass(tokens)
    instructions = parse_instruction(tokens)
    words, relocations = second_pass(instructions, symbol_table)
    write_object(words, symbol_table, relocations, obj_path)
    if not relocations:
        write_binary(words, output_path)
        return f"Generated {output_path} and {obj_path}"
    return f"Generated {obj_path}. Binary not generated because linking is required."

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input assembly file")
    parser.add_argument("--output", default="output.bin")
    args = parser.parse_args()
    bin_output = args.output
    if bin_output.endswith(".bin"):
        obj_output = bin_output[:-4] + ".obj"
    else:
        obj_output = bin_output + ".obj"
    result = assemble(args.input, bin_output, obj_output)
    print(result)
