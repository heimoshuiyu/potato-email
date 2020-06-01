import mail_sender, time, os, threading
from slog import logger
from config import data, kwd, save_json
from MessageRead import ReadMessage

################## 这个作为整合的主函数使用 ################

class Main:
    def __init__(self):
        self.newDay = 0

    def heartBeat(self):
        # 心跳功能，防止程序死的悄无声息
        now = time.localtime(time.time())
        if os.path.exists("./log/%s.txt" % (str(time.strftime("%Y%m%d", time.localtime())))) or self.newDay == 2:
            pass
        else:
            self.newDay = 1
            logger('本次启动时间为: %s' % (str(time.asctime( time.localtime(time.time()) ))),path="./log/")
            # 确保休眠到早上7点后再发心跳
            if (7 - now[3]) >= 0:
                time.sleep(3600*(7-now[3]-1) + 60*(60-now[4]))
            mail_sender.mail_sender.send("Dear Master, I am still alive! Take it easy.", "This is a Heartbeat function message. I'll send you every day so that you can know I'm there.")

    def main(self):
        while 1:
            # 此处写你的敏感信息
            data["o_usr"]=""
            data["o_pwd"]=""
            data["s_usr"]=""
            data["s_pwd"]=""
            thread = threading.Thread(target=self.heartBeat, args=(), daemon=True)
            thread.start()
            try:
                r = ReadMessage(data)

                #（成功则更新json文件）
                data["state"] = 0
                save_json()
                content_lst = r.read()
            
            except:
                time.sleep(10)
            
            # 用循环取出列表里的内容发送
            for content in content_lst:
                mail_sender.mail_sender.send(content[0], content[1])
            
            # 设置间隔时间
            r.clean_dic()
            save_json()
            time.sleep(60 * data["interval"])


if __name__ == '__main__':
    Main().main()


