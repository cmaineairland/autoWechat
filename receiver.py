from wxauto import WeChat
import time
import json

class Receiver:
    def __init__(self, listen_list):
        self.listen_list = listen_list
        self.wx = WeChat()
        self.wait = 1  
        for i in self.listen_list:
            self.wx.AddListenChat(who=i, savepic=False)

    def messageList(self):
        while True:
            msgs = self.wx.GetListenMessage()
            for chat in msgs:
                who = chat.who              
                one_msgs = msgs.get(chat)  
                # 回复收到
                for msg in one_msgs:
                    yield msg
                    """
                    msgtype = msg.type       
                    content = msg.content  
                    print(f'我与{who}的对话\n【sender】：{content}')
                
                    if msgtype == 'friend':
                        msg.quote('收到') 
                    """                  
            #time.sleep(self.wait)



if __name__ == '__main__':
    with open('setting.json', 'r', encoding='utf-8') as setting:
        settings = json.load(setting)
        listen_list = settings["listen_list"]

    r = Receiver(listen_list)
    #r.messageList()
    for message in r.messageList():
        print(message)





