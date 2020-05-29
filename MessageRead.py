import poplib, json, queue, time, mail_sender
from config import data, kwd
from re import sub
from email.parser import Parser
from email.utils import parseaddr
from email.header import decode_header
from slog import logger


############################## 这个类自带了日志功能，会记录下所有的错误 ##########################

################################  在其他文件里使用这个函数的例子  ####################################
#
# import MessageRead
# from config import data, kwd
# 
# r = ReadMessage(data)
# 
# （成功则更新json文件）
# data["state"] = 0
# r.json_write()
# content_lst = r.read()
#
# 这里的content_lst就是你要的内容列表辣！！
#
#
#
#
#
#
######################################## 这是整理过思路后的新解法 ########################################

class ReadMessage:
    def __init__(self, data):
        self.data = data
        self.newMail = queue.Queue() # 应该读取的邮件队列
        self.mail_queue = [] # 读取完等待发送的邮件列表
        self.clean()
        self.Content = '' # 邮件原文内容
        self.search = '' # 邮件处理大小写之后用于查询的内容
        self.title = '' # 邮件标题
        self.max = 0 # 设默认为空邮箱
        self.new = -1 # 默认更新json
    
    def clean(self):
        self.Content = '' # 邮件原文内容
        self.search = '' # 邮件处理大小写之后用于查询的内容
        self.title = '' # 邮件标题
    
    # 连接到pop服务器
    def Connect(self):
        # 连接到pop服务器
        server = poplib.POP3(self.data["o_server"])
        
        # 身份认证:
        server.user(self.data["o_usr"])
        server.pass_(self.data["o_pwd"])
        
        # 检测是否手动清理过邮箱，若是的话，更新json文件
        self.updata_json(server)
        
        #返回与服务器的连接
        return server
    
    # 检测是否手动清理过邮箱，若是的话，更新json文件。顺便计算出应该读取的新邮件数目
    def updata_json(self, server):
        # list()返回所有邮件的编号:
        resp, mails, octets = server.list()
        
        # 获取此时邮箱中的邮件数目
        self.max = len(mails) 
        
        self.new = self.max - self.data["max"]
        # 对比邮件数目，正常的话邮箱中的邮件会≥json中记录的邮件数目
        if self.new<0:
            self.data["max"] = self.max
            self.json_write()
        else:
            # 没有清理，计算出应该读取的邮件列表
            for i in range(self.new):
                self.newMail.put(self.max-i)
        
    # 更新json
    def json_write(self):
        # 转换类型再写入文件更新
        json_str = json.dumps(self.data)
        new = open("Info.json", "w+", encoding="utf-8")
        new.write(json_str)
        new.close()

    # 下载指定邮件并解析提取标题和内容
    def download(self, server, index):
        resp, lines, octets = server.retr(index)
    
        # lines存储了邮件原始文本所有内容
        msg_content = b'\r\n'.join(lines).decode('utf-8')
        
        # 把邮件内容解析为Message对象
        msg = Parser().parsestr(msg_content)
        
        # 解析邮件
        self.return_info(msg)
    
    # 解析邮件内容并返回标题、文本内容                       
    def return_info(self, msg, indent=0):
       # indent用于缩进，格式化输出
        if indent == 0:
           for header in ['From', 'To', 'Subject']:
               value = msg.get(header, '')
               if value:
                   if header=='Subject':
                       # 提取标题
                       value = self.decode_str(value)
                       self.title += value
                   else:
                       hdr, addr = parseaddr(value)
                       name = self.decode_str(hdr)
                       value = u'%s <%s>' % (name, addr)
                       value = sub('<[^<>]+>','',value)
                       v = sub('.{0}  +.{0}',' ',value)
               # print('%s%s: %s' % ('\t' * indent, header, value))
               self.Content += u'%s%s: %s\n' % ('\t'*indent, header, value)
               self.search += header.lower() + ': ' + v.lower() + '\n'
        
        # 检测是否有多个part
        if (msg.is_multipart()):
           parts = msg.get_payload()
           for n, part in enumerate(parts):
               # print('%spart %s' % ('\t' * indent, n))
               # print('%s--------------------' % ('\t' * indent))
               if n>0:
                return 0
               self.Content += u'%spart %s\n' % ('\t'*indent, str(n))
               self.Content += u'%s--------------------\n' % ('\t'*indent)
               self.return_info(part, indent + 1)
        else:
            content_type = msg.get_content_type()
            if content_type=='text/plain' or content_type=='text/html':
                content = msg.get_payload(decode=True)
                charset = self.guess_charset(msg)
                if charset:
                    content = content.decode(charset)
                    content = sub('<[^<>]+>','',content)
                    con = sub('.{0}  +.{0}','',content)
                # print('%sText: %s' % ('\t' * indent, content))
                self.search += '\t'*indent + con
                self.Content += u'%sText: %s\n' % ('\t'*indent, content)
            else:
                # print('%sAttachment: %s' % ('\t' * indent, content_type))
                pass
                self.Content += u'%sAttachment: %s\n' % ('\t'*indent, str(content_type))
    
    # 文本解码
    def decode_str(self, s):
        value, charset = decode_header(s)[0]
        if charset:
            value = value.decode(charset)
        return value
    
    # 检测文本编码方式是否为UTF-8
    def guess_charset(self, msg):
        charset = msg.get_charset()
        if charset is None:
            content_type = msg.get('Content-Type', '').lower()
            pos = content_type.find('charset=')
            if pos >= 0:
                charset = content_type[pos + 8:].strip()
        return charset
    
    # 循环读取新的未读邮件
    def read(self):
        logger('本次启动时间为: %s' % (str(time.asctime( time.localtime(time.time()) ))),path="./log/")
        print('1')
        server = self.Connect()
        
        # 判断未读邮件队列是否为空，看是否有新的未读邮件
        isEmpty = self.newMail.empty()
        while not isEmpty:
            try:
                newMail = self.newMail.get()
                print(newMail)
                self.download(server, newMail)
                for i in kwd:
                    if i in self.search: # 若文本或标题出现关键词，将内容放入待发送队列
                        self.mail_queue.append((self.title, self.Content))
                self.clean() # 每次读完一封邮件就把内容和标题清掉
                isEmpty = self.newMail.empty()
                
                # 如果正常读取，则设置状态为0（正常），并覆盖之前的状态码
                data["state"] = 0
                data["max"] += 1
                self.json_write()
                
            except Exception as e:
                logger('发生错误%s: %s' % (type(e), str(e)),path="./log/")
                self.newMail.put(newMail) # 失败的邮件重新放回发送队列
                
                # 邮件读取失败，状态码显示异常，每次加1；连续2小时出问题，则发一份警告
                if data["state"] < 32:
                    data["state"] += 1
                    self.json_write()
                elif data["state"] == 33:
                    mail_sender.send("Warning! Your assistance meet a problem!", "My dear master,\n\t I've got into a huge trouble! I need your help!\n\n\n\t Your lovely Potato Assistant (^_^).")
                else:
                    break
                time.sleep(10) # todo: 读取邮件出错，尝试重复读取的时间间隔
        
        # 返回一个待发送邮件列表
        return self.mail_queue      




 

################################# 这是段测试代码 ######################
        
if __name__ == "__main__":
    try:
        # 尝试读所有未读邮件
        r = ReadMessage(data)
        
        # 成功则更新json文件
        data["state"] = 0
        r.json_write()
        content_lst = r.read()
        
        # 打印出匹配到的第一则邮件
        print(content_lst[0][1])
    except:
        print("Error")
        
    



