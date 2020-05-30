import mail_sender, time, os, slog
from config import data, kwd
from MessageRead import ReadMessage

################## 这个作为整合的主函数使用 ################

def main():
    while 1:
        # 心跳功能，防止程序死的悄无声息
        if os.path.exists(u"./log/%s" % (str(time.strftime("%Y%m%d", time.localtime())))):
            pass
        else:
            mail_sender.mail_sender.send("Dear Master, I am still alive! Take it easy.", "This is a Heartbeat function message. I'll send you every day so that you can know I'm there.")
            slog.logger('本次启动时间为: %s' % (str(time.asctime( time.localtime(time.time()) ))),path="./log/")
        try:
            r = ReadMessage(data)

            #（成功则更新json文件）
            data["state"] = 0
            r.json_write()
            content_lst = r.read()
        
        except:
            time.sleep(10)
        
        # 用循环取出列表里的内容发送
        for content in content_lst:
            mail_sender.mail_sender.send(content[0], content[1])
        
        # 设置间隔时间
        time.sleep(60 * data["interval"])


if __name__ == '__main__':
    main()


