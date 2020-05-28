import poplib
from LFP import readInfo
from email.parser import Parser
from email.utils import parseaddr
from email.header import decode_header

def return_info(msg, indent=0):
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
       if (msg.is_multipart()):
           parts = msg.get_payload()
           for n, part in enumerate(parts):
               print('%spart %s' % ('  ' * indent, n))
               print('%s--------------------' % ('  ' * indent))
               return_info(part, indent + 1)
       else:
           content_type = msg.get_content_type()
           if content_type=='text/plain' or content_type=='text/html':
               content = msg.get_payload(decode=True)
               charset = guess_charset(msg)
               if charset:
                   content = content.decode(charset)
               print('%sText: %s' % ('  ' * indent, content + '...'))
               #return indent, content
           else:
               print('%sAttachment: %s' % ('  ' * indent, content_type))
               #return indent, content_type

def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value

def guess_charset(msg):
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset

def readMail(server, index=1):
    resp, lines, octets = server.retr(index)

    # lines存储了邮件原始文本所有内容
    msg_content = b'\r\n'.join(lines).decode('utf-8')
    
    # 把邮件内容解析为Message对象
    msg = Parser().parsestr(msg_content)
    
    

def download(data):
    # 连接到pop服务器
    server = poplib.POP3(data["o_server"])
    
    # 身份认证:
    server.user(data["o_usr"])
    server.pass_(data["o_pwd"])
    
    # list()返回所有邮件的编号:
    resp, mails, octets = server.list()
    
    # 获取邮件，注意编号是从1开始的
    # index = len(mails)
    readMail(server)
    
    
    # 关闭连接
    server.quit()
    
    return 
        
if __name__ == '__main__':
    title, content = download(readInfo("./Info.json"))
    input(title)



