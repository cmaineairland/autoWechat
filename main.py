import json
import threading
import time
from receiver import Receiver
import pythoncom
from queue import Queue
import LLMResponseFetcher
import init
import databaseController

messageQueue = Queue()
responseQueue = Queue()


def chooseTopic(dbController,sender):
    dbController.setTableName("topic")
    result=dbController.selectDataBy(("friend_remark","=",sender))
    for topic in result:
        if time.time()-float(topic.last_time)<36000000:
            return topic.id
    return False


def friendMessageProcessor(message,dbController,settings):
    #查询和发送者相关的对话
    topicID = chooseTopic(dbController,message.sender)
    if topicID:
        dbController.setTableName(topicID)
    else:
        topicID ="topic"+str(int(time.time()*1000))
        topicData = {
                        "id":topicID,
                        "friend_remark":message.sender,
                        "main":None,
                        "last_time":time.time()
                    }
        dbController.setTableName("topic")
        dbController.insertData(topicData)
        dbController.createTableBySettings(topicID,settings["databaseTablesDef"]["message_temp"])
    #选择一个小时内最近的对话
    #根据选择的对话创建或选择数据表，数据表以str(int(time.time()*1000))命名
    #数据表模板以message_temp为模板
    #一个小时内没有对话或用户选择结束对话，则写入topic数据表
    # 假设时间戳为 1640995200 （举例）
    
    sentenceBaseDataList = dbController.selectAllData()
    sentenceList=[]
    for sentence in sentenceBaseDataList:
        sentenceData ={
            "id":sentence.id,
            "content":sentence.content,
            "sender":sentence.sender,
            "time":sentence.time
        }
        sentenceList.append(sentenceData)
    #将对话数据发送给LLM
    

    receiveData =[message.sender,message.content,sentenceList]
    state,reasoningContent,response=LLMResponseFetcher.get(receiveData)
    if state:
        print("思考内容：")
        print(reasoningContent)
        print("回复内容：")
        print(response["reply"])

        responseQueue.put([response["reply"],message])
    timestamp = time.time()
    time_struct = time.localtime(timestamp)
    formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time_struct)
    sentenceData = {
                        "content":message.content,
                        "sender":message.sender,
                        "time":formatted_time,
                    }
    dbController.insertData(sentenceData)
    dbController.setTableName("topic")
    data={
        "last_time" :time.time(),
    }
    dbController.updateDataBy(data,("id","=",topicID))
    return topicID

def selfMessageProcessor(message,dbController,settings,topicID):
    print(topicID)
    if topicID:
        
        dbController.setTableName(topicID)
        timestamp = time.time()
        time_struct = time.localtime(timestamp)
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time_struct)
        if message.content.startswith("（注：本回答由AI自动回复，请注意甄别内容）"):
            message.sender = "Self(AI)"
        else:
            message.sender = "Self(not AI)"
        message.content = message.content.split("（注：本回答由AI自动回复，请注意甄别内容）", 1)[-1]
        message.content = message.content.split("\n引用  的消息 :", 1)[0].strip()
        sentenceData = {
                            "content":message.content,
                            "sender":message.sender,
                            "time":formatted_time,
                        }
        dbController.insertData(sentenceData)

def messageListener(r):
    for message in r.messageList():
        print(f"【{message.type}】监听到【{message.sender}】消息：{message.content}")
        print(message)      
        messageQueue.put(message)

        
    

def messageProcessor():
    topicID = False
    with open('setting.json', 'r', encoding='utf-8') as file:
        settings = json.load(file)
    dbController=databaseController.DatabaseController("AiAgent4WeChat.db")
    while True:
        if not messageQueue.empty():
            message = messageQueue.get()
            if message.type=='friend':
                topicID = friendMessageProcessor(message,dbController,settings)
            if message.type=='self':
                selfMessageProcessor(message,dbController,settings,topicID)
            if message.type=='group':
                continue
                #groupMessageProcessor(message,dbController,settings)
            else:
                continue

            
        time.sleep(1)

def messageSender():
    while True:
        if not responseQueue.empty():
            data = responseQueue.get()
            data[1].quote("（注：本回答由AI自动回复，请注意甄别内容）"+data[0])
        time.sleep(1)


def main():
    pythoncom.CoInitialize()
    with open('setting.json', 'r', encoding='utf-8') as file:
        settings = json.load(file)
    listen_list = settings["listen_list"]
    init.init()

    r = Receiver(listen_list)

    messageListenerThread = threading.Thread(target=messageListener,args=(r,),daemon=True)
    messageProcessorThread = threading.Thread(target=messageProcessor,daemon=True)
    messageSenderThread = threading.Thread(target=messageSender,daemon=True)


    messageListenerThread.start()
    print("系统正在启动...")
    time.sleep(10)
    while not messageQueue.empty():
        messageQueue.get()
    print("系统启动成功！")
    messageProcessorThread.start()
    messageSenderThread.start()

    try:
        while True:
            time.sleep(999999999)
    except KeyboardInterrupt:
        pythoncom.CoUninitialize()
        exit()

if __name__ == "__main__":
    main()
    