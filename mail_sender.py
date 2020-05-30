# 需要的参数有：mail_host mail_user mail_pass
# 须知：
#
# class Mail_sender
#   # 无阻塞发送邮件方法，传入标题和内容
#   def send(self, title='Title', content='Text')
#
# 示例
# from mail_sender import mail_sender
# mail_sender.send(title='I am title', content='I am content')
# 或者
# mail_sender.send('I am title', 'I am content')
# 

import smtplib
import queue
import threading
import time
import email
import email.mime.text
import config

class Mail_sender:
    def __init__(self):
        self.mail_host = config.data.get('s_host')
        self.mail_user = config.data.get('s_usr')
        self.mail_pass = config.data.get('s_pwd')
        self.send_queue = queue.Queue()
        self.smtpobj = None

        # 启动发送邮件线程
        self.thread = threading.Thread(target=self.send_thread, args=(), daemon=True)
        self.thread.start()
    
    # 发送邮件函数（无阻塞）
    def send(self, title='Title', content='Text'):
        mail = Mail(title, content)
        self.send_queue.put(mail)
        
    # 循环发送邮件线程
    def send_thread(self):
        while True:
            mail = self.send_queue.get()
            try:
                self.init_and_send(mail)
            except Exception as e:
                print('发生错误%s: %s' % (type(e), str(e)))
                self.send_queue.put(mail) # 失败的邮件重新放回发送队列
                time.sleep(10) # todo: 从json中读取发生错误尝试重复发送的时间间隔
            finally:
                time.sleep(5) # todo: 从接送中读取发送邮件的时间间隔
            

    # 初始化并登录smtp服务器
    def init_and_send(self, mail):
        print('\n%s' % ('**'*20))
        print('\nstart sending') # todo 记录日志
        self.smtpobj = smtplib.SMTP()
        self.smtpobj.connect(self.mail_host, 465)
        
        self.smtpobj.login(self.mail_user, self.mail_pass)
        print('\ninit over')

        self.smtpobj.sendmail(self.mail_user, self.mail_user, self.to_string(mail))
        print('\nsend over')
        
        print('\n%s' % ('**'*20))

    # 将Mail结构转化成SMTP协议可以读取的字符串结构
    def to_string(self, mail):
        message = email.mime.text.MIMEText(mail.content, 'plain', 'utf-8')
        message['From'] = email.header.Header(self.mail_user, 'utf-8')
        message['To'] = email.header.Header(self.mail_user, 'utf-8')
        message['Subject'] = email.header.Header(mail.title, 'utf-8')
        return message.as_string()



# 用来储存邮件信息的结构体
class Mail:
    def __init__(self, title, content):
        self.title = title
        self.content = content

# 测试用代码
if __name__ == '__main__':
    mail_sender = Mail_sender()

    while True:
        title = input('仅供测试用，请输入标题\n')
        print(config.data['s_host'])
        message = 'test'
        mail_sender.send(title, message)

# 实例化Mail_sender，供外部调用
mail_sender = Mail_sender()
