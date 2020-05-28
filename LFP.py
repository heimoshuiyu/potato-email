# Local File Process
import os, json, time

# 用于读取用户基本信息（如账号密码等）
def readInfo(file):
    info = open(file, "r", encoding="utf-8").read()
    # 解析json
    data = json.loads(info)
    return data


if __name__ == '__main__':
    data = readInfo("./Info.json")
    input(data)
    



