START:  MOV R0, #5
        MOV R1, #3
        ADD R2, R0, R1
        SUB R3, R2, #1

        CMP R3, #0
        TST R3, R1

        MUL R4, R0, R1

        STR R4, [R5]
        LDR R6, [R5, #8]

        B LOOP

LOOP:   ADD R0, R0, #1
        CMP R0, #10
        B LOOP