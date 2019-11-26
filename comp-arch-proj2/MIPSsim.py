# -*- coding: utf-8 -*-
# @Time    : 2019/11/29 21:38
# @Author  : amy_Zhoucc
# @File    : MIPSsim.py
# @note    :On my honor, I have neither given nor received unauthorized aid on this assignment.

import sys

# 基准地址
BEGIN_ADDR = 256
# 指令长度
INSTRUCTION_LEN = 4
# 数据长度
DATA_LEN = 4
# 数据字长
BIN_DATA_LEN = 32

# 存放寄存器当前的值
registers = [
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0
]
# 以字典形式，存放汇编指令，格式是 指令地址: 指令 eg：256: 'ADD R1, R0, R0'
instruction = {}
# 以字典形式，存放数据，格式是 数据地址：数据 eg：348: -3
data = {}


# category-1指令转换
# 'xxxx'匹配，则进入到对应的函数中，将机器码对应的翻译出汇编指令，返回一个字符串，注意机器码翻译出来的寄存器的顺序有些不同
# J,BEQ, BLTZ, BGTZ的立即数要经过处理才能用
category_1 = {
    '0000': lambda bin_instr: 'J #%d' % (int(bin_instr[6:32] + '00', 2)),  # imm 意义为无条件跳转到指定pc地址（pc地址无负号，所以是无符号数）
    '0001': lambda bin_instr: 'JR R%d' % (int(bin_instr[6:11], 2)),  # rs  意义为无条件跳转到指定pc地址，地址存放在寄存器中
    '0010': lambda bin_instr: 'BEQ R%d, R%d, #%d' % (
        int(bin_instr[6:11], 2), int(bin_instr[11:16], 2), bin2dec(bin_instr[16:32] + '00')),
    # rs rt off -> rs rt off 意义为若rs = rt 就基于此跳转off量(off是signed)
    '0011': lambda bin_instr: 'BLTZ R%d, #%d' % (int(bin_instr[6:11], 2), bin2dec(bin_instr[16:32] + '00')),
    # rs off -> rs off 意义为若rs < 0，就基于此跳转off量（off是signed）
    '0100': lambda bin_instr: 'BGTZ R%d, #%d' % (int(bin_instr[6:11], 2), bin2dec(bin_instr[16:32] + '00')),
    # rs off -> rs off 意义为若rs > 0，就基于此跳转off量（off是signed）
    '0101': lambda bin_instr: 'BREAK',
    '0110': lambda bin_instr: 'SW R%d, %d(R%d)' % (
        int(bin_instr[11:16], 2), bin2dec(bin_instr[16:32]), int(bin_instr[6:11], 2)),
    # base rt off -> rt off(base) base is a register 意义为将寄存器的值存放在内存中（off是signed）
    '0111': lambda bin_instr: 'LW R%d, %d(R%d)' % (
        int(bin_instr[11:16], 2), bin2dec(bin_instr[16:32]), int(bin_instr[6:11], 2)),
    # base rt off -> rt off(base) base is a register 意义为将内存中的值存放在寄存器（off是signed）
    '1000': lambda bin_instr: 'SLL R%d, R%d, #%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[11:16], 2), int(bin_instr[21:26], 2)),
    # rt rd sa -> rd rt sa sa是无符号数   rt向左逻辑移位sa位（空出来的位，补0）
    '1001': lambda bin_instr: 'SRL R%d, R%d, #%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[11:16], 2), int(bin_instr[21:26], 2)),
    # rt rd sa -> rd rt sa sa是无符号数   rt向右逻辑移位sa位（空出来的位，补0）
    '1010': lambda bin_instr: 'SRA R%d, R%d, #%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[11:16], 2), int(bin_instr[21:26], 2)),
    # rt rd sa -> rd rt sa sa是无符号数   rt向右算术移位sa位（空出来的位，补符号数）
    '1011': lambda bin_instr: 'NOP'
}
# category-2指令转换
# 'xxxx'匹配，则进入到对应的函数中，将机器码对应的翻译出汇编指令，返回一个字符串，注意机器码翻译出来的操作对象的顺序有些不同
# 逻辑运算指令，注意翻译出来的寄存器编号的顺序
category_2 = {
    '0000': lambda bin_instr: 'ADD R%d, R%d, R%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),
    # rs rt rd -> rd rs rt  意义为 rd <- rs + rt
    '0001': lambda bin_instr: 'SUB R%d, R%d, R%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),
    # rs rt rd -> rd rs rt  意义为 rd <- rs - rt
    '0010': lambda bin_instr: 'MUL R%d, R%d, R%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),
    # rs rt rd -> rd rs rt  意义为 rd <- rs * rt
    '0011': lambda bin_instr: 'AND R%d, R%d, R%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),
    # rs rt rd -> rd rs rt  意义为 rd <- rs and rt
    '0100': lambda bin_instr: 'OR R%d, R%d, R%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),
    # rs rt rd -> rd rs rt  意义为 rd <- rs or rt
    '0101': lambda bin_instr: 'XOR R%d, R%d, R%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),
    # rs rt rd -> rd rs rt  意义为 rd <- rs xor rt
    '0110': lambda bin_instr: 'NOR R%d, R%d, R%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),
    # rs rt rd -> rd rs rt  意义为 rd <- rs nor rt
    '0111': lambda bin_instr: 'SLT R%d, R%d, R%d' % (
        int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),
    # rs rt rd -> rd rs rt  意义为若 rs < rt 返回1->rd 否则返回0->rd
    '1000': lambda bin_instr: 'ADDI R%d, R%d, #%d' % (
        int(bin_instr[11:16], 2), int(bin_instr[6:11], 2), bin2dec(bin_instr[16:32])),
    # rs rt imm ->rt rs imm 意义为 rt <- rs + imm(signed)
    '1001': lambda bin_instr: 'ANDI R%d, R%d, #%d' % (
        int(bin_instr[11:16], 2), int(bin_instr[6:11], 2), int(bin_instr[16:32], 2)),
    # rs rt imm ->rt rs imm 意义为 rt <- rs and imm(是16位，左边扩展16位，以对齐，本质上是无符号数，但是翻译还是当成符号数翻译)
    '1010': lambda bin_instr: 'ORI R%d, R%d, #%d' % (
        int(bin_instr[11:16], 2), int(bin_instr[6:11], 2), int(bin_instr[16:32], 2)),
    # rs rt imm ->rt rs imm 意义为 rt <- rs or imm(是16位，左边扩展16位，以对齐，本质上是无符号数)
    '1011': lambda bin_instr: 'XORI R%d, R%d, #%d' % (
        int(bin_instr[11:16], 2), int(bin_instr[6:11], 2), int(bin_instr[16:32], 2)),
    # rs rt imm ->rt rs imm 意义为 rt <- rs xor imm(是16位，左边扩展16位，以对齐，本质上是无符号数)
}
# 区分category-1和category-2，根据指令最前面2位，分别进入到不同的函数中
instruction = {
    '01': lambda bin_instr: category_1[bin_instr[2:6]](bin_instr),  # category-1根据指令的2-5位（共4位），判断具体是哪个指令
    '11': lambda bin_instr: category_2[bin_instr[2:6]](bin_instr),  # category-2
}

# 模拟计算机对category-2中的 算术逻辑指令 进行具体操作
simluation_cate_2 = {
    "ADD": lambda rs, rt: rs + rt,  # 寄存器加操作 rs + rt -> rd
    "SUB": lambda rs, rt: rs - rt,  # 寄存器减操作 rs - rt -> rd
    "MUL": lambda rs, rt: rs * rt,  # 寄存器乘操作 rs * rt -> rd
    "AND": lambda rs, rt: rs & rt,  # 寄存器与操作 rs & rt -> rd
    "OR": lambda rs, rt: rs | rt,  # 寄存器或操作
    "XOR": lambda rs, rt: rs ^ rt,  # 寄存器异或操作
    "NOR": lambda rs, rt: ~(rs | rt),  # 寄存器或非操作
    "SLT": lambda rs, rt: 1 if rs < rt else 0,  # 寄存器值比较操作 如果rs < rt，返回1；反之，返回0
    "ADDI": lambda rs, imm: rs + imm,  # 寄存器+立即数操作
    "ANDI": lambda rs, imm: rs & imm,  # 寄存器-立即数操作
    "ORI": lambda rs, imm: rs | imm,  # 寄存器或立即数操作
    "XORI": lambda rs, imm: rs ^ imm  # 寄存器异或立即数操作
}

#一些缓冲区和标志
waiting_instr = ""
execute_instr = ""
pre_ISSUE = []          #IF--issue之间的缓冲区，数目<= 4
pre_ALU1 = []          #issue--alu1之间的缓冲区，存放lw/sw指令，数目<= 2
pre_ALU2 = []          #issue--alu2之间的缓冲区，存放alu指令，数目<= 2
pre_MEM = {"instruction": "", "mem_addr":""}          #alu1--mem之间的缓冲区，存放lw/sw指令+结果，数目<= 1
post_ALU2 = {"instruction":"", "value":""}         #alu2--wb之间的缓冲区，存放alu指令+结果，数目<= 1
post_MEM = {"instruction":"", "value":""}            #mem--wb之间的缓冲区，存放lw的寄存器id和结果，数目<= 1
# scoreboard
reg_write_status = [True, True, True, True, True, True, True, True,
                   True, True, True, True, True, True, True, True,
                   True, True, True, True, True, True, True, True,
                   True, True, True, True, True, True, True, True]         #记录所有寄存器当前读的状态，默认全为True(可用)
reg_branch_status = ["", "", "", "", "", "", "", "",
                   "", "", "", "", "", "", "", "",
                   "", "", "", "", "", "", "", "",
                   "", "", "", "", "", "", "", ""]         #记录所有寄存器当前读的状态，默认全为""(空)

reg_read_status = [True, True, True, True, True, True, True, True,
                   True, True, True, True, True, True, True, True,
                   True, True, True, True, True, True, True, True,
                   True, True, True, True, True, True, True, True]       #记录所有寄存器当前写的状态，默认全为True(可用)
# 标志: stall标志,默认false(不存在stall), pc(指令地址值, 存放的是即将要fetch的指令地址), break标志(是否出现了break)
stall_flag = False
pc = BEGIN_ADDR
break_flag = False
pre_alu1_reg = ""
pre_alu2_reg = ""
store_flag = True
# 针对分支指令的执行
def execute_branch(instr):
    global pc, stall_flag
    stall_flag = False
    #分解指令,获得操作码
    instr_list = instr.replace(",", "").split(" ")
    opera = instr_list[0]
    #形如: J #%d
    if opera == 'J':
        pc = int(instr_list[1].replace('#', ''))
    #形如: JR R%d
    elif opera == 'JR':
        operand = int(instr_list[1].replace('R', ''))
        #如果该寄存器的值是有在write的,就不能读取
        if not reg_write_status[operand] or reg_branch_status[operand]:
            stall_flag = True
            #说明不可执行
            return False
        else:
            pc = registers[operand]
    #形如: BEQ R%d, R%d, #%d
    elif opera == 'BEQ':
        operand1 = int(instr_list[1].replace('R', ''))
        # print(operand1)
        operand2 = int(instr_list[2].replace('R', ''))
        # print(operand2)
        if not reg_write_status[operand1]or reg_branch_status[operand1] or reg_branch_status[operand2]:
            # print("in")
            stall_flag = True
            return False
        elif registers[operand1] == registers[operand2]:
            pc += int(instr_list[3].replace('#', ''))
    #形如: BLTZ R%d, #%d
    elif opera == 'BLTZ':
        operand= int(instr_list[1].replace('R', ''))
        if not reg_write_status[operand] or reg_branch_status[operand]:
            stall_flag = True
            return False
        elif registers[operand] < 0:
            pc += int(instr_list[2].replace('#', ''))
    #形如: BGTZ R%d, #%d
    elif opera == 'BGTZ':
        # print("in")
        operand = int(instr_list[1].replace('R', ''))
        if not reg_write_status[operand] or reg_branch_status[operand]:
            stall_flag = True
            return False
        elif registers[operand] > 0:
            pc += int(instr_list[2].replace('#', ''))
    return True


# 取指令单元，非分支指令/break/nop,结果存放在pre_ISSUE中,这三类指令存现取现处理
# 需要的是原始指令{0:"ADD R3, R5, R6", 1:"LW R5,34(R4)"} -> wait/execute 或是 pre_issue:[]
def IF_unit():
    IF_out = []
    global stall_flag, execute_instr, waiting_instr, pc, break_flag         #全局变量
    IF_num = 0                                                              #fetch计数
    execute_instr = ""                                                      #清空正在execute_instr
    #如果上一周期是stall状态的,即为true
    # print(stall_flag)
    if stall_flag:
        instr = waiting_instr                                               #从waiting_instr中取指令,看这一周期是否可执行
        if execute_branch(instr):                                           #若可执行,就将wait移到execute中,并将wait清空
            execute_instr = instr
            waiting_instr = ""
    else:
        #如果已经fetch的指令<2,且后一缓冲区未满,且未出现break
        while not break_flag and IF_num < 2 and (len(IF_out) + len(pre_ISSUE)) < 4:
            instr = instruction[pc]
            pc += INSTRUCTION_LEN
            instr_list = instr.replace(',', '').split(' ')
            if instr_list[0] == 'BREAK':
                execute_instr = "BREAK"
                break_flag = True
            elif instr_list[0] == 'NOP':
                continue
            elif instr_list[0] in ('J', 'JR', 'BEQ', 'BLTZ', 'BGTZ'):
                not_stall = execute_branch(instr)
                if not_stall:
                    #可执行,放入execute中
                    execute_instr = instr
                else:
                    #不可执行, 放入wait中
                    waiting_instr = instr
                #如果是分支指令,一周期只有一条
                break
            else:
                if instr_list[0] != "SW":
                    # print("in")
                    reg_branch_status[int(instr_list[1].replace('R',''))] += instr_list[0]+" "
                # pre_ISSUE.append(instr)
                IF_out.append(instr)
                IF_num += 1
    return  IF_out


def get_opera_operand(instr):
    instr_list = instr.replace(',', '').split(' ')
    opera = instr_list[0]
    if opera in ("LW", "SW"):
        operand1 = int(instr_list[1].replace('R', ''))
        operand2 = int(instr_list[2].split('(')[1].replace(')', '').replace('R', ''))
        return opera, operand1, operand2
    elif opera in ("ADD", "SUB", "MUL", "AND", "OR", "XOR", "NOR", "SLT"):
        operand1 = int(instr_list[1].replace('R', ''))
        operand2 = int(instr_list[2].replace('R', ''))
        operand3 = int(instr_list[3].replace('R', ''))
        return opera, operand1, operand2, operand3
    elif opera in ("ADDI", "ANDI", "ORI", "XORI", 'SLL', 'SRL', 'SRA'):
        operand1 = int(instr_list[1].replace('R', ''))
        operand2 = int(instr_list[2].replace('R', ''))
        return opera, operand1, operand2

def WARHazard(index):
    cur_instr = pre_ISSUE[index]
    cur_instr_tup = get_opera_operand(cur_instr)
    if cur_instr_tup[0] == 'SW':                #不存在写入寄存器，直接判定为false
        return False
    operand1 = cur_instr_tup[1]
    for i in range(0, index):
        prev_instr = pre_ISSUE[i]
        prev_instr_tup = get_opera_operand(prev_instr)
        if len(prev_instr_tup) == 4:                 #如果为寄存器间操作
            prev_operand2 = prev_instr_tup[2]
            prev_operand3 = prev_instr_tup[3]
            if prev_operand2 == operand1 or prev_operand3 == operand1:
                return True
        if len(prev_instr_tup) == 3:                 #如果含有立即数
            if prev_instr_tup[0] == 'SW':       #存在2个read数
                prev_operand1 = prev_instr_tup[1]
                prev_operand2 = prev_instr_tup[2]
                if prev_operand1 == operand1 or prev_operand2 == operand1:
                    return True
            else:
                prev_operand2 = prev_instr_tup[2]
                if prev_operand2 == operand1:
                    return True
    return False

def WAWHazard(index):
    cur_instr = pre_ISSUE[index]
    cur_instr_tup = get_opera_operand(cur_instr)
    if cur_instr_tup[0] == 'SW':
        return False
    operand1 = cur_instr_tup[1]
    for i in range(0, index):
        prev_instr = pre_ISSUE[i]
        prev_instr_tup = get_opera_operand(prev_instr)
        if prev_instr_tup[0] == 'SW':
            continue
        prev_operand1 = prev_instr_tup[1]
        if prev_operand1 == operand1:
            #存在冒险
            return True
    #不存在冒险
    return False

def RAWHazard(index):
    cur_instr = pre_ISSUE[index]
    cur_instr_tup = get_opera_operand(cur_instr)
    for i in range(0, index):
        prev_instr = pre_ISSUE[i]
        prev_instr_tup = get_opera_operand(prev_instr)
        if prev_instr_tup[0] == 'SW':
            continue
        prev_operand1 = prev_instr_tup[1]
        if len(cur_instr_tup) == 4:
            operand2 = cur_instr_tup[2]
            operand3 = cur_instr_tup[3]
            if prev_operand1 == operand2 or prev_operand1 == operand3:
                return True
        if len(cur_instr_tup) == 3:
            if cur_instr_tup[0] == 'SW':
                operand1 = cur_instr_tup[1]
                operand2 = cur_instr_tup[2]
                if prev_operand1 == operand1 or prev_operand1 == operand2:
                    return True
            else:
                operand2 = cur_instr_tup[2]
                if prev_operand1 == operand2:
                    return True
    return False

# 判断是否某一条指令是否能issue
#参数: 指令,指令在pre_issue的位置, store指令标志
def judge_issue(instr, instr_index):
    # print(reg_write_status)
    # print(instr_index)
    global store_flag
    instr_list = instr.replace(',', '').split(' ')
    opera = instr_list[0]
    issue_flag = False              #判断当前指令能否issue的标志,默认为false:不能
    cur_store_flag = store_flag
    #形如: 'ADD R%d, R%d, R%d'
    if opera in ("ADD", "SUB", "MUL", "AND", "OR", "XOR", "NOR", "SLT"):
        # print("in")
        operand1 = int(instr_list[1].replace('R', ''))
        operand2 = int(instr_list[2].replace('R', ''))
        operand3 = int(instr_list[3].replace('R', ''))
        #分别避免了 WAW, RAW, WAR
        if reg_write_status[operand1] and reg_read_status[operand1] and reg_write_status[operand2] and reg_write_status[operand3] and not WARHazard(instr_index) and not WAWHazard(instr_index) and not RAWHazard(instr_index):
            # print("in")
            reg_write_status[operand1] = False
            reg_read_status[operand2] = False
            reg_read_status[operand3] = False
            issue_flag = True
    #形如: 'ADDI R%d, R%d, #%d'
    elif opera in ("ADDI", "ANDI", "ORI", "XORI", 'SLL', 'SRL', 'SRA'):
        # print(opera)
        operand1 = int(instr_list[1].replace('R', ''))
        operand2 = int(instr_list[2].replace('R', ''))
        if reg_write_status[operand1] and reg_read_status[operand1] and reg_write_status[operand2] and not WARHazard(instr_index) and not WAWHazard(instr_index) and not RAWHazard(instr_index):
            reg_write_status[operand1] = False
            reg_read_status[operand2] = False
            issue_flag = True
    # 形如: SW R%d, %d(R%d)
    # 要求所有所有的store已经发出
    elif opera == 'LW':
        # print(opera)
        operand1 = int(instr_list[1].replace('R', ''))
        operand2 = int(instr_list[2].split('(')[1].replace(')', '').replace('R', ''))
        if reg_write_status[operand1] and reg_read_status[operand1] and reg_write_status[operand2] and store_flag and not WARHazard(instr_index) and not WAWHazard(instr_index) and not RAWHazard(instr_index):
            reg_write_status[operand1] = False
            reg_read_status[operand2] = False
            issue_flag = True
    # store顺序发送
    elif opera == 'SW':
        operand1 = int(instr_list[1].replace('R', ''))
        operand2 = int(instr_list[2].split('(')[1].replace(')', '').replace('R', ''))
        if reg_write_status[operand1] and reg_write_status[operand2] and store_flag and not WARHazard(instr_index) and not WAWHazard(instr_index) and not RAWHazard(instr_index):
            reg_read_status[operand1] = False
            reg_read_status[operand2] = False
            issue_flag = True
        else:
            cur_store_flag = False
    return issue_flag, cur_store_flag


# 指令发布单元，结果分开存放：pre_ISSUE -> issue -> pre_ALU1_queue(LW/SW);pre_ALU2_queue(others)
# pre_ISSUE: []
def issue_unit():
    ISSUE_out1 = []
    ISSUE_out2 = []
    # print(pre_ISSUE)
    global store_flag
    index = 0               #记录当前指令在pre_issue中的位置
    issue_alu1_num = 0      #记录已经issue到alu1的个数
    issue_alu2_num = 0      #记录已经issue到alu2的个数
    store_flag = True       #记录是否已经遇到store指令
    while len(pre_ISSUE) != 0 and index < len(pre_ISSUE):
        instr = pre_ISSUE[index]
        opera = instr.replace(',', '').split(' ')[0]
        # pre_alu1或者pre_alu2满,就无法issue指定的指令
        if opera in ("LW", "SW"):
            index += 1
            #如果pre_ALU1已满,或者已经issue一条,就不再issue LW/SW指令
            if len(pre_ALU1) == 2 or issue_alu1_num == 1:
                continue
            issue_flag, cur_store_flag = judge_issue(instr, index - 1)
            if issue_flag:
                ISSUE_out1.append(instr)
                # pre_ALU1.append(instr)
                pre_ISSUE.remove(instr)
                issue_alu1_num = 1
            store_flag = store_flag and cur_store_flag
        else:
            index += 1
            # 如果pre_ALU2已满,或者已经issue一条,就不再issue ALU指令
            if len(pre_ALU2) == 2 or issue_alu2_num == 1:
                continue
            issue_flag, cur_store_flag = judge_issue(instr, index - 1)
            if issue_flag:
                ISSUE_out2.append(instr)
                # pre_ALU2.append(instr)
                pre_ISSUE.remove(instr)
                issue_alu2_num = 1
            store_flag = store_flag and cur_store_flag
        if ISSUE_out1 != []:
            instr_list = get_opera_operand(ISSUE_out1[0])
            reg_read_status[instr_list[2]] = True
            if instr_list[0] == "SW":
                reg_read_status[instr_list[1]] = True

    return ISSUE_out1, ISSUE_out2


# 计算单元1：计算LW/SW pre_ALU1_queue -> ALU1 -> pre_MEM_buffer
# 使用的参数：pre_ALU1，形如["LW R4, 23(R5)"]
# 更新的pre_ALU1, pre_MEM，形如：['LW R4, 23(R5)'], {'instruction': 'SW R5, 25(R2)', 'mem_addr': '29'}
def ALU1_unit():
    ALU1_out = ()
    # pre_ALU1不为空，说明有需要计算的LW/SW的地址值，计算完成后，把该指令pop出去，并更新1号指令变为0号
    if pre_ALU1 != []:
        instr = pre_ALU1[0]
        inst_list = instr.replace(',', '').split(' ')
        if inst_list[0] == 'LW' or inst_list[0] == 'SW':
            source_num = inst_list[2].split('(')
            imm = int(source_num[0])
            source_reg = int(source_num[1].replace(')', '').replace('R', ''))
            addr = imm + registers[source_reg]
            reg_read_status[source_reg] = True
            # reg_read_status[]
            pre_ALU1.remove(instr)
            ALU1_out = (instr, str(addr))
            # pre_MEM["instruction"] = instr
            # pre_MEM["mem_addr"] = str(addr)
    return ALU1_out

# 计算单元2：计算others pre_ALU2_queue -> ALU2 -> post_ALU2_buffer
# 使用到的参数：pre_ALU2，形如["ADD R4, R3, R5", "SUB R3, R7, R2"]
# 更新pre_ALU2, post_ALU2, 形如["SUB R3, R7, R2"], {"instruction": instr, "value": str(value)}
def ALU2_unit():
    ALU2_out = ()
    if pre_ALU2 != []:
        instr = pre_ALU2[0]
        value = execute_alu2_instr(instr)
        ALU2_out = (instr, str(value))
        # post_ALU2["instruction"] = instr
        # post_ALU2["value"] = str(value)
        pre_ALU2.remove(instr)
    return ALU2_out


# 读/存数据单元：store/load: pre_MEM_buffer -> MEM -> post_MEM_buffer(LW)/none(SW)
# 使用到的参数pre_MEM，形如： ({"instruction": "LW R5, 34(R4)", "mem_addr":"368"})
# 更新当前post_MEM，形如：{"instruction": "LW R5, 34(R4)", 'value': '-2'}
def MEM_unit():
    MEM_out = ()
    # pre_MEM不为空，则说明有load/store需要执行
    if pre_MEM['instruction'] != '':
        instr = pre_MEM["instruction"]
        instr_list = instr.replace(',', '').split(' ')
        if instr_list[0] == 'LW':
            addr = int(pre_MEM["mem_addr"])
            value = data[addr]
            MEM_out = (instr, str(value))
            # post_MEM["instruction"] = instr
            # post_MEM["value"] = str(value)
        elif instr_list[0] == 'SW':
            addr = int(pre_MEM["mem_addr"])
            register_id = int(instr_list[1].replace("R",""))
            data[addr] = registers[register_id]
        pre_MEM['instruction'] = ''
        pre_MEM['mem_addr'] = ''
    return MEM_out


# 写回单元：更新寄存器中的值 post_MEM_buffer(LW)/post_ALU2(others) -> WB
# post_ALU2 = {"instruction":"", "value":""}  post_MEM = {"instruction": "LW R5, 34(R4)", "value":""}  register_status = [...]
# 用到的参数有post_MEM,post_ALU2,register_status,形如：({"instruction": "LW R5, 34(R4)", "value":"12"}, {"instruction":"ADD R1, R2, R3", "value":"25"}, {'R0': '', 'R1': 'ADD', 'R2': '', 'R3': '', 'R4': '', 'R5': 'LW'})
def WB_unit():
    # global pre_alu1_reg, pre_alu2_reg
    # if pre_alu1_reg != '':
    #     reg_write_status[int(pre_alu1_reg)] = True
    # if pre_alu2_reg != '':
    #     reg_write_status[int(pre_alu2_reg)] = True
    # 如果post_MEM中有内容，即需要写回，并且将对应的寄存器的状态置为空
    if post_MEM['instruction'] != '':
        # print(post_MEM)
        instr =  post_MEM["instruction"]
        instr_list = instr.replace(', ', ' ').split(' ')
        register_id = int(instr_list[1].replace("R", ""))
        registers[register_id] = int(post_MEM["value"])
        pre_alu1_reg = str(register_id)
        post_MEM['instruction'] = ''
        post_MEM['value'] = ''
        # print(instr_list[0]+" ")
        reg_branch_status[register_id] = reg_branch_status[register_id].replace(instr_list[0]+" ", "")
        reg_write_status[register_id] = True

    # 如果post_ALU2中有内容，需要写回，并且将对应的寄存器的状态置为空
    if post_ALU2['instruction'] != '':
        instr = post_ALU2["instruction"]
        instr_list = instr.replace(', ', ' ').split(' ')
        register_id = int(instr_list[1].replace("R", ""))
        registers[register_id] = int(post_ALU2["value"])
        pre_alu2_reg = str(register_id)
        post_ALU2['instruction'] = ''
        post_ALU2['value'] = ''
        # print(instr_list[0]+" ")
        reg_branch_status[register_id] = reg_branch_status[register_id].replace(instr_list[0]+" ", "")
        reg_write_status[register_id] = True


# 参数：二进制数字
# 将补码的二进制数字转换成十进制数
def bin2dec(bin_num):
    if bin_num[0] == '0':  # 如果首位为0，为非负数
        dec_num = int(bin_num[1:], 2)  # 直接调用函数
    else:  # 如果首位为1，则为负数，先取反，再+1，获得负数的原码，然后再翻译，注意前面有个负号
        revers_num = ''
        for num in bin_num[1:]:
            if num == "0":
                revers_num += "1"
            else:
                revers_num += "0"
        dec_num = -(int(revers_num, 2) + 1)
    return dec_num


# 参数:十进制数字，移动方向，移动位数
# 将寄存器中的十进制数字转换位补码的二进制数，再进行逻辑移位操作，再将其变成十进制数字返回
# 返回：移位好的十进制数字
def move_logic(dec_num, move_direct, move_num):
    move_bin = ""
    if dec_num < 0:  # 先判断十进制数是正数or负数
        dec_num += 1
        bin_dec = bin(dec_num)  # 先将其转换为二进制 -0bxxxxx
        bin_dec = bin_dec.replace("-0b", "")  # 将前缀去掉
        rev_bin = ""
        for i in range(0, BIN_DATA_LEN - len(bin_dec)):
            rev_bin += "1"  # 将前面不足的位数，用符号位（1）补足
        for num in bin_dec:  # 变成补码形式
            if num == '1':
                rev_bin += '0'
            else:
                rev_bin += '1'
    else:
        bin_dec = bin(dec_num)
        bin_dec = bin_dec.replace("0b", "")
        rev_bin = ""
        for i in range(0, BIN_DATA_LEN - len(bin_dec)):  # 将前面补足的位数，用符号位（0）补足
            rev_bin += "0"
        rev_bin += bin_dec

    if move_direct == "left":  # 判断移位方向
        move_bin += rev_bin[move_num:]  # 根据移动位数，取后面的32-num位，前面的num放弃
        for i in range(0, move_num):  # 用0补足后面的num位数
            move_bin += '0'
    if move_direct == "right":
        for i in range(0, move_num):  # 用0补足前面的num位
            move_bin += '0'
        for i in range(0, BIN_DATA_LEN - move_num):  # 取前面的32-num位，后面的num位放弃
            move_bin += rev_bin[i]
    return bin2dec(move_bin)


# 翻译机器指令变成汇编语句的函数
# 参数：全部的机器码
# 返回值：机器指令+指令地址+翻译出来的汇编 按照指定的格式输出
def handle_code(binary_code):
    current_loc = BEGIN_ADDR  # current_loc保存当前指令存放的地址，第一个地址就是题目指定的初始地址
    flag_code = True  # 判断当前译码的是指令还是数据
    assembly_code = ''  # 存放完成译码的指令或是数据
    for bin_instr in binary_code.split('\n'):  # 将指令一条一条的读取，以\n作为指令之间的分界
        # print(bin_instr)
        if bin_instr == '':  # 最后一行是空格，如果继续处理会报错，所以将之排除
            continue
        if flag_code:  # 当在处理指令时
            tran_ass = instruction[bin_instr[0:2]](bin_instr)  # 翻译指令：先根据机器码的前2位，判断是 算术逻辑指令or 非算术逻辑指令 -> 进入到不同的指令处理区
            assembly_code += "%s\t%d\t%s\n" % (bin_instr, current_loc, tran_ass)  # 按照指定格式存放，每一行三列：原机器码\t指令存放的位置\t汇编指令
            instruction[current_loc] = tran_ass  # 将翻译好的汇编指令存放在字典中，方便后面仿真的时候调用 指令地址: 指令名
            if tran_ass == "BREAK":  # 如果当前读取的是BREAK指令，意味着后面就是数据区了
                flag_code = False
                data_loc = current_loc + INSTRUCTION_LEN  # 数据指示地址，在处理数据时需要用到
                global data_addr
                data_addr = data_loc  # 获得数据基地址，为一个全局变量，以方便其他函数调用
            current_loc += INSTRUCTION_LEN  # 更新当前指令地址
            # print(tran_ass)
        else:
            dec_num = bin2dec(bin_instr)  # 将二进制的补码翻译成十进制数字
            assembly_code += "%s\t%d\t%s\n" % (bin_instr, current_loc, dec_num)  # 按照指定格式存放，每一行三列：原机器码\t指令存放的位置\t汇编指令
            data[data_loc] = dec_num  # 将翻译好的数据存放在字典中，方便后面仿真的时候调用 数据地址：数据
            data_loc += DATA_LEN
            current_loc += DATA_LEN  # 更新当前指令存放
    return assembly_code


# 参数：每一条指令，当前的PC值
# 计算机模拟每一条不同的指令的执行过程
# 返回执行该指令后pc的值和break标志
def execute_alu2_instr(instr):
    # flag_break = False  # 判断程序是否终止的标志，是出现BREAK，就意味着程序终止了; True：程序终止；False:程序未终止
    instr_part = instr.replace(', ', ' ').split(' ')  # 将指令进行切割，执行数之间是通过“，”相隔，而执行数和操作数之间是通过空格，所以统一换成空格，再进行切割
    if instr_part[0] in ("ADD", "SUB", "MUL", "AND", "OR", "XOR", "NOR",
                         "SLT"):  # 若操作指令是 寄存器算术逻辑指令 的一个   格式统一为 operand rd,rs,rt （ADD R2,R1,R5）
        rs_data = registers[int(instr_part[2].replace("R", ""))]  # 获取当前rs寄存器中的值，eg："R6" -> "6" -> 6 -> register[6]
        rt_data = registers[int(instr_part[3].replace("R", ""))]  # 获取当前rt寄存器中的值，"R4"
        value = simluation_cate_2[instr_part[0]](rs_data, rt_data)  # 得到rs、rt操作后的值，存放在rd_data中

        reg_read_status[int(instr_part[2].replace("R", ""))] = True
        reg_read_status[int(instr_part[3].replace("R", ""))] = True
        # registers[int(instr_part[1].replace("R", ""))] = rd_data  # 将rd_data的值传入register[rd]中
        # pc += INSTRUCTION_LEN  # pc向下移位

    elif instr_part[0] in (
            "ADDI", "ANDI", "ORI", "XORI"):  # 若操作指令是 寄存器-立即数算术逻辑指令 的一个 格式统一为 operand rd rs imm （ADDI R2,R4,#34）
        rs_data = registers[int(instr_part[2].replace("R", ""))]  # 获取register[rs]
        imm_data = int(instr_part[3].replace("#", ""))  # 获取立即数的值
        value = simluation_cate_2[instr_part[0]](rs_data, imm_data)  # 将rs、imm操作后的值，存放在rd_data中
        reg_read_status[int(instr_part[2].replace("R", ""))] = True

    elif instr_part[0] in ('SLL', 'SRL',
                           'SRA'):  # 移位操作 SLL/SRL/SRA 逻辑左移/逻辑右移/算术右移(先逻辑右移，再把最高为复制)   operand rd rt sa -> SLL R3,R4,#2/SRL R5,R6,#3/SRA R1,R16,#2
        rt = int(instr_part[2].replace("R", ""))  # 获取rt
        rd = int(instr_part[1].replace("R", ""))  # 获取rd
        sa = int(instr_part[3].replace("#", ""))  # 获取sa
        if instr_part[0] == 'SLL':
            value = move_logic(registers[rt], "left", sa)  # 逻辑左移，并赋值
        elif instr_part[0] == 'SRL':
            value = move_logic(registers[rt], "right", sa)  # 逻辑右移并赋值
        else:
            value = registers[rt] >> sa  # 算术右移
        reg_read_status[int(instr_part[2].replace("R", ""))] = True
        # pc += INSTRUCTION_LEN
    # elif instr_part[0] == 'NOP':  # 不进行任何操作
    #     pc += INSTRUCTION_LEN
    return value


def format_buffer():
    output = "IF Unit:\n"
    instr = waiting_instr
    if instr != "":
        instr = " [%s]" % instr
    output += "\tWaiting Instruction:%s\n" % instr
    instr = execute_instr
    if instr != "":
        instr = " [%s]" % instr
    output += "\tExecuted Instruction:%s\n" % instr
    output += "Pre-Issue Queue:\n"
    for i in [0, 1, 2, 3]:
        instr = ""
        if i < len(pre_ISSUE):
            instr = " [%s]" % pre_ISSUE[i]
        output += "\tEntry %d:%s\n" % (i, instr)
    output += "Pre-ALU1 Queue:\n"
    for i in [0, 1]:
        instr = ""
        if i < len(pre_ALU1):
            instr = " [%s]" % pre_ALU1[i]
        output += "\tEntry %d:%s\n" % (i, instr)
    instr = ""
    if pre_MEM['instruction'] != "":
        instr = " [%s]" % pre_MEM['instruction']
    output += "Pre-MEM Queue:%s\n" % instr
    instr = ""
    if post_MEM['instruction'] != "":
        instr = " [%s]" % post_MEM["instruction"]
    output += "Post-MEM Queue:%s\n" % instr
    output += "Pre-ALU2 Queue:\n"
    for i in [0, 1]:
        instr = ""
        if i < len(pre_ALU2):
            instr = " [%s]" % pre_ALU2[i]
        output += "\tEntry %d:%s\n" % (i, instr)
    instr = ""
    if post_ALU2['instruction'] != "":
        instr = " [%s]" % post_ALU2["instruction"]
    output += "Post-ALU2 Queue:%s\n\n" % instr
    return output

# 将执行过程按照指定要求输出
# 参数：当前执行步数，当前pc值
# 返回：str格式的输出formated_output
def format_output(cycle):
    output = "--------------------\nCycle:%d\n\n" % (cycle)
    buffer_output = format_buffer()
    output += buffer_output
    output += "Registers\n"\
              "R00:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" \
              "R08:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" \
              "R16:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" \
              "R24:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n\nData\n" % (tuple(registers))
    data_output = ""
    i = 0
    data_loc = data_addr
    for data_v in data.values():
        if i == 0 or i % 8 == 0:
            data_output += str(data_loc) + ':\t%d\t' % (data_v)
        elif i % 8 == 7 and i != 0:
            data_output += '%d\n' % (data_v)
        else:
            data_output += '%d\t' % (data_v)
        data_loc += DATA_LEN
        i += 1
    if i % 8 != 0:
        output += data_output + '\n'
    else:
        output += data_output
    return output


# 模拟计算机流水线执行指令
def pipeline_simulation():
    cycle = 1       #记录当前执行的步数
    global pc
    pc = BEGIN_ADDR #pc的开始地址
    output = ""
    while True:
        if_out = IF_unit()
        issue_out1, issue_out2 = issue_unit()
        alu1_out = ALU1_unit()
        alu2_out = ALU2_unit()
        mem_out = MEM_unit()
        WB_unit()
        pre_ISSUE.extend(if_out)
        # print(pre_ISSUE)
        pre_ALU1.extend(issue_out1)
        pre_ALU2.extend(issue_out2)
        if alu1_out != ():
            pre_MEM["instruction"] = alu1_out[0]
            pre_MEM["mem_addr"] = alu1_out[1]
        if alu2_out != ():
            post_ALU2["instruction"] = alu2_out[0]
            post_ALU2["value"] = alu2_out[1]
        if mem_out != ():
            post_MEM["instruction"] = mem_out[0]
            post_MEM["value"] = mem_out[1]

        # print(cycle)
        # # print("pc: "+str(pc))
        # print(reg_write_status)
        # print(reg_read_status)
        # print(reg_branch_status)
        output += format_output(cycle)
        cycle += 1
        if break_flag:
            break
        # if cycle == 80:
        #     break
    return output


# 参数：输出的内容，文件路径
# 将输出的内容，写入文件
def write_file(output, file_path):
    try:
        out_file = open(file_path, "w")  # 可写形式，打开文件
    except:
        print("can't open the file!")  # 打不开抛出异常，程序结束
        sys.exit(1)
    try:
        out_file.write(output)  # 写入内容
    except:
        print("can't write to the file!")  # 写不了抛出异常，程序结束
        sys.exit(1)
    finally:
        out_file.close()  # 关闭文件


# 参数：文件路径;
# 返回：文件内容，str格式
# 打开文件
def read_File(file_path):
    try:
        binary_file = open(file_path, "r")  # 只读形式，打开文件
    except:
        print("can't open the file!")  # 打不开则抛出异常，程序结束
        sys.exit(1)
    try:
        binary_code = binary_file.read()  # 读取文件内容，存放在binary_code中
    except:
        print("can't read the file!")  # 读不了则抛出异常，程序结束
        sys.exit(1)
    finally:
        binary_file.close()  # 将文件关闭
    # print(binary_code)
    return binary_code


if __name__ == '__main__':
    filename = sys.argv;  # 用户自行输入需要译码的文件名字
    # filename = "sample.txt"
    binary_code = read_File(filename[1])  # 读取存放机器指令的文件
    assemble_code = handle_code(binary_code)  # 处理读取出来的机器指令进行反汇编
    write_file(assemble_code, './disassembly.txt')  # 将翻译好的汇编指令写入指定文件
    simulation_output = pipeline_simulation()
    write_file(simulation_output, './simulation.txt')