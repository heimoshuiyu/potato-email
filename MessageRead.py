import poplib, json, queue, time, mail_sender
from config import data, kwd, save_json
from re import sub, search, compile, findall
from email.parser import Parser
from email.utils import parseaddr
from email.header import decode_header
from slog import logger


############################## 功能介绍 ##########################

# 这个类自带了日志功能，会记录下所有的错误
# 有[1:精确查找  2:模糊查找  3:联合+精确查找  4:联合+模糊查找]的功能 (联合查找用++分隔追加条件，用(你的条件)的格式写你要减掉的条件并放在每行最后(不需要用空格隔开))
# 可以在一行的最前面加**，可以单行进行精确搜索（实现全局上的精确/模糊/联合搜索）
# 注意!模糊查找的速度会变慢！

################################  在其他文件里使用这个函数的例子  ####################################
#
# from MessageRead import ReadMessage
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
    
    # 删除字典敏感信息
    def clean_dic(self):
        ls = ["o_usr","o_pwd","s_usr","s_pwd"]
        for i in ls:
            del self.data[i]
    
    # 初始化邮件内容、标题
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
                       v = value
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
                    con = sub('[\r\n]','',con)
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
    
    # 模糊查找算法
    def fuzzy_search(self, word):
        co_in = []
        new_ls = [i for i in word]
        
        # 省略2个以内字符的模糊查找
        # pt1 = compile('.{1}')
        # new1 = '[^' '].{0,2}'.join(pt1.findall(word))
        # co_in.append(search(new1, self.search))
        
        # 打错2个或省略1个字符的模糊查找
        new2 = []
        if len(new_ls) < 1:
            return False
        if len(new_ls) < 3:
            if word in self.search:
                print("匹配词为：%s;" % word)
                return True
            else:
                return False
                
        for i in range(1,len(new_ls)-1):
            ch = new_ls[i]
            new_ls[i] = "[^' '.]{0,2}"
            new2.append(''.join(new_ls))
            new_ls[i] = ch

        for i in new2:
            if search(i, self.search) != None:
                # print("匹配词为：%s;  匹配项为：%s" % (word, i)) ### 调试用语句
                co_in.append(True)
            else:
                co_in.append(False)
        # 若有匹配项目,则返回真
        if True in co_in:
            print("匹配词为：%s;" % word)
            return True
        else:
            return False
    
    # 查词模式[1:精确查找  2:模糊查找  3:联合+精确查找  4:联合+模糊查找]
    def search_wd(self, word):
        if len(word) == 0:
            return False
        # 精确查找
        if self.data["mode"] == 1:
            return (word in self.search)
        
        # 模糊查找
        elif self.data["mode"] == 2:
            return self.fuzzy_search(word)
            
        # 联合+精确查找
        elif self.data["mode"] == 3:
            try:
                try:
                    w_pls = word.split("(")[0]
                    w_pls = w_pls.split("++")
                except:
                    w_pls = word.split("++")
                try:
                    pattern = compile("[(].+?[)]")
                    w_sls = pattern.findall(word)
                    for i in range(len(w_sls)):
                        w_sls[i] = w_sls[i].replace("(","")
                        w_sls[i] = w_sls[i].replace(")","")
                except:
                    pass
            except:
                w_pls = word
            co_in = []
            for i in w_pls:
                if len(i) == 0:
                    return False
                co_in.append(i in self.search)
            for i in w_sls:
                if len(i) == 0:
                    return True
                co_in.append(not i in self.search)
            try:
                for i in w_sls:
                    co_in.append(not i in self.search)
            except:
                pass
            if False in co_in:
                return False
            else:
                return True
        
        # 联合+模糊查找
        else:
            
            try:
                try:
                    w_pls = word.split("(")[0]
                    w_pls = w_pls.split("++")
                except:
                    w_pls = word.split("++")
                try:
                    pattern = compile("[(].+?[)]")
                    w_sls = pattern.findall(word)
                    for i in range(len(w_sls)):
                        w_sls[i] = w_sls[i].replace("(","")
                        w_sls[i] = w_sls[i].replace(")","")
                except:
                    pass
            except:
                w_pls = word
            co_in = []
            for i in w_pls:
                co_in.append(self.fuzzy_search(i))
            try:
                for i in w_sls:
                    co_in.append(not self.fuzzy_search(i))
            except:
                pass
            if False in co_in:
                # print("一票否决")
                return False
            else:
                return True
        
    
    # 循环读取新的未读邮件
    def read(self):
        logger('本次启动时间为: %s' % (str(time.asctime( time.localtime(time.time())))),path="./log/")
        print('Start reading -- %s' % (str(time.asctime( time.localtime(time.time())))))
        server = self.Connect()
        
        # 判断未读邮件队列是否为空，看是否有新的未读邮件
        isEmpty = self.newMail.empty()
        while not isEmpty:
            try:
                newMail = self.newMail.get()
                print(newMail)
                self.download(server, newMail)
                mode = self.data["mode"]
                for i in kwd:
                    if "**" in i:
                        self.data["mode"] = 3  
                    
                    if "(" in i:
                        try:
                            subword = i.split("(")
                            if subword[0] == '':
                                subword[1] = subword[1].replace(")","")
                            print("%s-%s-%s"%(subword,"##"*25,str(subword in self.search)))
                            if subword[1] in self.search:
                                break
                        except:
                            pass
                    if self.search_wd(i): # 若文本或标题出现关键词，将内容放入待发送队列
                        print("%s's mail should be sent. Subject: %s"%(newMail, self.title))
                        self.mail_queue.append((self.title, self.Content))
                        break
                self.clean() # 每次读完一封邮件就把内容和标题清掉
                isEmpty = self.newMail.empty()
                data["mode"] = mode # 把搜索模式设置回去
                
                # 如果正常读取，则设置状态为0（正常），并覆盖之前的状态码
                data["state"] = 0
                data["max"] += 1
                self.json_write()
                
            except Exception as e:
                logger(u'发生错误%s: %s' % (type(e), str(e)),path="./log/")
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
        
        # 打印出匹配到的第一则邮件
        print("\n\t%s  下面是会被发送的邮件：  %s\n" % ("**"*10, "**"*10))
        if self.mail_queue == []:
            print("\tNone")
        for i in self.mail_queue:
            print(i[0])
        print("\n\t%s"% ("***"*20))
        # 返回一个待发送邮件列表
        return self.mail_queue      




 

################################# 这是段测试代码 ######################
        
if __name__ == "__main__":
    try:
        # 尝试读所有未读邮件
        r = ReadMessage(data)
        
        # 成功则更新json文件
        data["state"] = 0
        save_json()
        content_lst = []
        content_lst = r.read()
        
        # 打印出匹配到的第一则邮件
        print(content_lst[0][1])
        input()
    except:
        input("Error")
        
    



