REGISTERS = {
    "R0": 0, "R1": 1, "R2": 2, "R3": 3,
    "R4": 4, "R5": 5, "R6": 6, "R7": 7,
    "R8": 8, "R9": 9, "R10": 10, "R11": 11,
    "R12": 12,
    "R13": 13, "R14": 14, "R15": 15,
    "SP": 13, "LR": 14, "PC": 15
}

CONDITIONS = {
    "AL": 0b1110
}

DATA_PROCESSING_OPCODES = {
    "AND": 0b0000,
    "EOR": 0b0001,
    "SUB": 0b0010,
    "ADD": 0b0100,
    "TST": 0b1000,
    "CMP": 0b1010,
    "ORR": 0b1100,
    "MOV": 0b1101,
    "MVN": 0b1111,
}

LOAD_STORE_OPCODES = {
    "STR": 0,
    "LDR": 1
}

INSTRUCTION_SET = {
    "ADD": {"class": "data_processing", "opcode": DATA_PROCESSING_OPCODES["ADD"]},
    "SUB": {"class": "data_processing", "opcode": DATA_PROCESSING_OPCODES["SUB"]},
    "AND": {"class": "data_processing", "opcode": DATA_PROCESSING_OPCODES["AND"]},
    "ORR": {"class": "data_processing", "opcode": DATA_PROCESSING_OPCODES["ORR"]},
    "EOR": {"class": "data_processing", "opcode": DATA_PROCESSING_OPCODES["EOR"]},
    "MOV": {"class": "data_processing", "opcode": DATA_PROCESSING_OPCODES["MOV"]},
    "MVN": {"class": "data_processing", "opcode": DATA_PROCESSING_OPCODES["MVN"]},
    "CMP": {"class": "data_processing", "opcode": DATA_PROCESSING_OPCODES["CMP"]},
    "TST": {"class": "data_processing", "opcode": DATA_PROCESSING_OPCODES["TST"]},
    "B":   {"class": "branch"},
    "BL":  {"class": "branch"},
    "LDR": {"class": "load_store"},
    "STR": {"class": "load_store"},
    "MUL": {"class": "multiply"}
}

OPERAND_TYPE = {
    "REGISTER": 0,
    "IMMEDIATE": 1
}

FLAG_ONLY_INSTRUCTIONS = {"CMP", "TST"}