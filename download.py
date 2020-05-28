import poplib, json
from LFP import readInfo
from email.parser import Parser
from email.utils import parseaddr
from email.header import decode_header
from mail_sender import mail_sender.send

def return_info(msg, Content, indent=0):
       title=''
       if indent == 0:
           for header in ['From', 'To', 'Subject']:
               value = msg.get(header, '')
               if value:
                   if header=='Subject':
                       value = decode_str(value)
                   else:
                       hdr, addr = parseaddr(value)
                       name = decode_str(hdr)
                       value = u'%s <%s>' % (name, addr)
               print('%s%s: %s' % ('  ' * indent, header, value))
               Content += '  '*indent + header + ': ' + value + '\n'
       if (msg.is_multipart()):
           parts = msg.get_payload()
           for n, part in enumerate(parts):
               print('%spart %s' % ('  ' * indent, n))
               print('%s--------------------' % ('  ' * indent))
               Content += '  ' * indent + 'part ' + str(n) +'\n'
               Content += '  ' * indent + '--------------------\n'
               return_info(part, Content, indent + 1)
       else:
           content_type = msg.get_content_type()
           if content_type=='text/plain' or content_type=='text/html':
               content = msg.get_payload(decode=True)
               charset = guess_charset(msg)
               if charset:
                   content = content.decode(charset)
               print('%sText: %s' % ('  ' * indent, content + '...'))
               Content += '  ' * indent + 'Text: ' + content + '.\n'
               #return indent, content
           else:
               print('%sAttachment: %s' % ('  ' * indent, content_type))
               Content += '  ' * indent + 'Attachment: ' + str(content_type) + '\n'
               #return indent, content_type
       return title, Content     

# 文本解码
def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value

# 检测文本编码方式是否为UTF-8
def guess_charset(msg):
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset

# 读单封邮件并解析提取标题和内容
def readMail(server, index=1):
    Content=''
    resp, lines, octets = server.retr(index)

    # lines存储了邮件原始文本所有内容
    msg_content = b'\r\n'.join(lines).decode('utf-8')
    
    # 把邮件内容解析为Message对象
    msg = Parser().parsestr(msg_content)
    
    # 解析邮件
    title, Content = return_info(msg, Content)
    
    # 返回标题和文本内容
    return title, Content

# 更新json
def json_write(data):
    json_str = json.dumps(data)
    new = open("Info.json", "w+", encoding="utf-8")
    new.write(json_str)
    new.close()


# 下载邮件
def download(data):
    # 连接到pop服务器
    server = poplib.POP3(data["o_server"])
    
    # 身份认证:
    server.user(data["o_usr"])
    server.pass_(data["o_pwd"])
    
    # list()返回所有邮件的编号:
    resp, mails, octets = server.list()
    
    # 获取邮件，注意编号是从1开始的
    index = len(mails) # index是最大邮件数
    if data["max"]>index:
        data["max"] = index
        json_write(data)
    else:
        title, Content = readMail(server)
    
    
    # 关闭连接
    server.quit()
    
    return title, Content
        
if __name__ == '__main__':
    try:
        data = readInfo("./Info.json")
        title, content = download(data)
        data["state"] = 0
        json_write(data)
    except:
        if data["state"] < 32:
            data["state"] += 1
            json_write(data)
        elif data["state"] = 33:
            send("Warning! Your assistance meet a problem!", "My dear master,\n\t I've got into a huge trouble! I need your help!\n\n\n\t Your lovely Potato Assistant (^_^).")
        else:
            pass
        
    input(content)



