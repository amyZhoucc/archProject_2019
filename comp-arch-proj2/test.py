import difflib
import sys

BIN_DATA_LEN = 8
def bin2dec(bin_num):
    if bin_num[0] == '0':               #如果首位为0，为非负数
        dec_num = int(bin_num[1:],2)    #直接调用函数
    else:                               #如果首位为1，则为负数，先取反，再+1，获得负数的原码，然后再翻译，注意前面有个负号
        revers_num = ''
        for num in bin_num[1:]:
            if num == "0":
                revers_num += "1"
            else:
                revers_num += "0"
        dec_num = -(int(revers_num,2) + 1)
    return dec_num

def move_logic(dec_num, move_direct, move_num):
    move_bin = ""
    if dec_num < 0:                                             #先判断十进制数是正数or负数
        dec_num += 1
        bin_dec = bin(dec_num)                                  #先将其转换为二进制 -0bxxxxx
        bin_dec = bin_dec.replace("-0b", "")                    #将前缀去掉
        rev_bin = ""
        for i in range(0, BIN_DATA_LEN - len(bin_dec)):
            rev_bin += "1"                                      #将前面不足的位数，用符号位（1）补足
        for num in bin_dec:                                     #变成补码形式
            if num == '1':
                rev_bin += '0'
            else:
                rev_bin += '1'
    else:
        bin_dec = bin(dec_num)
        bin_dec = bin_dec.replace("0b", "")
        rev_bin = ""
        for i in range(0, BIN_DATA_LEN - len(bin_dec)):         #将前面补足的位数，用符号位（0）补足
            rev_bin += "0"
        rev_bin += bin_dec

    if move_direct == "left":                                   #判断移位方向
        move_bin += rev_bin[move_num:]                          #根据移动位数，取后面的32-num位，前面的num放弃
        for i in range(0, move_num):                            #用0补足后面的num位数
            move_bin += '0'
    if move_direct == "right":
        for i in range(0, move_num):                            #用0补足前面的num位
            move_bin += '0'
        for i in range(0, BIN_DATA_LEN - move_num):             #取前面的32-num位，后面的num位放弃
            move_bin += rev_bin[i]
    print(move_bin)
    return bin2dec(move_bin)
def read_file(file_name):
    try:
        file_handle = open(file_name, 'r')
        text = file_handle.read().splitlines()  # 读取后以行进行分割
        file_handle.close()
        return text
    except IOError as error:
        print('Read file Error: {0}'.format(error))
        sys.exit()

if __name__ == '__main__':
    # print(move_logic(-15, "left", 2))
    # instr = "SW R3, 3(R4)"
    # instr_list = instr.replace(',', '').split(' ')
    # operand2 = int(instr_list[2].split('(')[1].replace(')', '').replace('R', ''))
    # print(operand2)
    # tu = (2,3)
    # print(len(tu))
    # i = ["sfsreg", "efewge"]
    # o = []
    # i.extend(o)
    # print(i)
    # sd = ("eg","fwer")
    # if sd != ():
    #     print(sd)
    i = "sdf"
    r = 'r12'

    print(r.replace('r',''))
    file1_name = "simulation.txt"
    file2_name = "simulation3.txt"
    # diff = difflib.ndiff(open(file1).readlines(), open(file2).readlines())
    # print (''.join(diff),)

    if file1_name == "" or file2_name == "":
        print('文件路径不能为空：file1_name的路径为：{0}, file2_name的路径为：{1} .'.format(file1_name, file2_name))
        sys.exit()
    text1_lines = read_file(file1_name)
    text2_lines = read_file(file2_name)
    diff = difflib.HtmlDiff()  # 创建htmldiff 对象
    result = diff.make_file(text1_lines, text2_lines)  # 通过make_file 方法输出 html 格式的对比结果
    #  将结果保存到result.html文件中并打开
    try:
        with open('result.html', 'w') as result_file:  # 同 f = open('result.html', 'w') 打开或创建一个result.html文件
            result_file.write(result)  # 同 f.write(result)
    except IOError as error:
        print('写入html文件错误：{0}'.format(error))




