import os
import pandas as pd
import re


# 读取当前目录的文件名
def get_files_name(path):
    files_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            files_list.append(os.path.join(root, file))
    return files_list


# 读取本地excle文件
def read_xlsx(file_name):
    # 传入文件名，读取excle文件
    xls = pd.ExcelFile(file_name)
    # 把第一个工作表除第一行外，读作问题信息
    question = xls.parse(0)
    return question


if __name__ == "__main__":
    files_name = get_files_name("answers")
    for name in files_name:
        xls = read_xlsx(name)
