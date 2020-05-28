# 有这个config.py文件，就可以在不同py文件中共享一份json字典啦
# 在a.py中对字典做的更改可以直接被b.py读取到
# 用法示例
# 
# 载入
# import config
#
# 读取操作字典
# print(config.jsondata['key'])
# 
# 读取关键词列表
# print(config.ksd)
#
# 设置字典键值对
# config.jsondata['key'] = value
#
# 保存字典到json
# config.save_json()
#
# 保存关键词到txt文件
# config.save_txt()

import json


JSON_FILENAME = 'Info.json'
KWD_FILENAME = 'kwd.txt'

with open(JSON_FILENAME, 'r') as f:
    jsondata = json.loads(f.read())

with open(KWD_FILENAME, 'r') as f:
    __kwd_str = f.read()
__kwd_str = __kwd_str.replace('\r', '')
kwd = __kwd_str.split('\n')


def save_json():
    with open(JSON_FILENAME, 'w') as f:
        f.write(json.dumps(jsondata))

def save_kwd():
    with open(KWD_FILENAME, 'w') as f:
        __kwd_str = '\n'.join(kwd)
        f.write(__kwd_str)

