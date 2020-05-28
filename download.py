import poplib, json, threading, queue, time
from LFP import readInfo
from email.parser import Parser
from email.utils import parseaddr
from email.header import decode_header
from slog import logger
#from mail_sender import mail_sender.send

# 启动线程开始循环读邮件
class LoopRead:
    def __init__(self, data):
        self.data = data
        self.content_queue = queue.Queue()
        
        # 启动线程
        self.thread = threading.Thread(target=self.read_thread, args=(), daemon=True)
        self.thread.start()
    
    # 循环读取邮件线程
    def read_thread(self):
        while True:
            content = ReadMessage(self.data)
            try:
                self.content_queue.put(content)
            except Exception as e:
                logger('发生错误%s: %s' % (type(e), str(e)),path="./log/")
                self.content_queue.put(content) # 失败的邮件重新放回发送队列
                time.sleep(10) # todo: 读取邮件出错，尝试重复读取的时间间隔
            finally:
                time.sleep(self.data["interval"]) # todo: 从接送中读取发送邮件的时间间隔


# 读取邮件信息
class ReadMessage:
    def __init__(self, data):
        self.title = ''
        self.data = data
        self.content_queue = queue.Queue()
        self.Content = ''
        
        # 启动线程
        self.thread = threading.Thread(target=self.download, args=(), daemon=True)
        self.thread.start()
    
    # 解析邮件内容并返回标题、文本内容                       
    def return_info(self, msg, indent=0):
       # 初始化标题为空字符串
       if indent == 0:
           for header in ['From', 'To', 'Subject']:
               value = msg.get(header, '')
               if value:
                   if header=='Subject':
                       value = self.decode_str(value)
                   else:
                       hdr, addr = parseaddr(value)
                       name = self.decode_str(hdr)
                       value = u'%s <%s>' % (name, addr)
               print('%s%s: %s' % ('  ' * indent, header, value))
               self.Content += '  '*indent + header + ': ' + value + '\n'
       if (msg.is_multipart()):
           parts = msg.get_payload()
           for n, part in enumerate(parts):
               print('%spart %s' % ('  ' * indent, n))
               print('%s--------------------' % ('  ' * indent))
               self.Content += '  ' * indent + 'part ' + str(n) +'\n'
               self.Content += '  ' * indent + '--------------------\n'
               self.return_info(part, indent + 1)
       else:
           content_type = msg.get_content_type()
           if content_type=='text/plain' or content_type=='text/html':
               content = msg.get_payload(decode=True)
               charset = self.guess_charset(msg)
               if charset:
                   content = content.decode(charset)
               print('%sText: %s' % ('  ' * indent, content + '...'))
               self.Content += '  ' * indent + 'Text: ' + content + '.\n'
               #return indent, content
           else:
               print('%sAttachment: %s' % ('  ' * indent, content_type))
               self.Content += '  ' * indent + 'Attachment: ' + str(content_type) + '\n'
               #return indent, content_type     

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
    
    # 读单封邮件并解析提取标题和内容
    def readMail(self, server, index=1):
        resp, lines, octets = server.retr(index)
    
        # lines存储了邮件原始文本所有内容
        msg_content = b'\r\n'.join(lines).decode('utf-8')
        
        # 把邮件内容解析为Message对象
        msg = Parser().parsestr(msg_content)
        
        # 解析邮件
        self.return_info(msg, Content)
        
    
    # 更新json
    def json_write(self):
        # 转换类型再写入文件
        json_str = json.dumps(self.data)
        new = open("Info.json", "w+", encoding="utf-8")
        new.write(json_str)
        new.close()
    
    
    # 下载邮件
    def download(self):
        # 连接到pop服务器
        server = poplib.POP3(self.data["o_server"])
        
        # 身份认证:
        server.user(self.data["o_usr"])
        server.pass_(self.data["o_pwd"])
        
        # list()返回所有邮件的编号:
        resp, mails, octets = server.list()
        
        # 获取邮件，注意编号是从1开始的
        index = len(mails) # index是最大邮件数
        if self.data["max"]>index:
            self.data["max"] = index
            self.json_write(self.data)
        else:
            self.readMail(server)
        
        
        # 关闭连接
        server.quit()
        
        # 返回标题和文本内容
        return self.title, self.Content
    
    # 读邮件（无阻塞）
    def read(self):
        title, Content = self.download()
        lr = LoopRead(self.data)
        lr.content_queue.put(Content)
        
        # 返回标题和文本内容
        return self.title, self.Content
        
if __name__ == '__main__':
    try:
        # 读取基本信息
        data = readInfo("./Info.json")
        
        # 进行邮件分析
        r = ReadMessage(data)
        title, Content = r.read()
        
        # 如果正常读取，则设置状态为0（正常），并覆盖之前的状态码
        data["state"] = 0
        r.json_write()
    except:
        # 邮件读取失败，状态码显示异常，每次加1；连续2小时出问题，则发一份警告
        if data["state"] < 32:
            data["state"] += 1
            r.json_write()
        elif data["state"] == 33:
            pass #send("Warning! Your assistance meet a problem!", "My dear master,\n\t I've got into a huge trouble! I need your help!\n\n\n\t Your lovely Potato Assistant (^_^).")
        else:
            pass
        
    input(content)



