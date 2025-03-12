import json
import threading
import time
from receiver import Receiver
import pythoncom
from queue import Queue
import LLMResponseFetcher
import init
import databaseController
def chooseTopic(dbController,sender):
    dbController.setTableName("topic")
    result=dbController.selectDataBy(("friend_remark","=",sender))
    for topic in result:
        if time.time()-float(topic.last_time)<3600:
            return topic.id
    return False
with open('setting.json', 'r', encoding='utf-8') as file:
    settings = json.load(file)
dbController=databaseController.DatabaseController("AiAgent4WeChat.db")
print(chooseTopic(dbController,"王雷潇"))
print(str(int(time.time()*1000)),settings["databaseTablesDef"]["message_temp"])
sender = "王雷潇"
topicID = chooseTopic(dbController,sender)
if topicID:
    dbController.setTableName(topicID)
else:
    topicID ="topic"+str(int(time.time()*1000))
    topicData = {"id":topicID,
                    "friend_remark":sender,
                    "main":None,
                    "last_time":time.time()
                    }
    dbController.setTableName("topic")
    dbController.insertData(topicData)
    dbController.createTableBySettings(topicID,settings["databaseTablesDef"]["message_temp"])
print(dbController)
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
print(sentenceList)