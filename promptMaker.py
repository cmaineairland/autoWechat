import json
import sqlite3
import datetime


def getPrompt(data,method):
    if method=='getMessageReply':
        with open('prompt/getMessageReply.json', 'r', encoding='utf-8') as prompt:
            prompt = json.load(prompt)
        with open('setting.json', 'r', encoding='utf-8') as settings:
            settings = json.load(settings)
        conn = sqlite3.connect('AiAgent4WeChat.db')
        cursor = conn.cursor()
        query = "SELECT * FROM friend_info WHERE remark =?"
        cursor.execute(query, (data[0],))
        friendInfo = cursor.fetchall()

        friendInfoTemplate = prompt["friendInfo"]
        data_mapping = list(friendInfoTemplate)
        friendInfoList = []
        for entry in friendInfo:
            friend_info = friendInfoTemplate.copy()  # 复制模板，防止修改原模板
            # 使用循环来将数据按顺序填充到对应字段
            for idx, field in enumerate(data_mapping):
                if idx < len(entry):  # 防止越界
                    friend_info[field]["content"] = entry[idx]
            friendInfoList.append(friend_info)
        prompt["friendInfo"] = friendInfoList
        prompt["message"]['content']= data[1]
        prompt["myInfo"]= settings["myInfo"]
        prompt["topicInfo"]=data[2]
        prompt["message"]["timestamp"]=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        print(prompt)
        return prompt

if __name__ == '__main__':
    data =["王雷潇","我想去北京",[{'id': 1, 'content': '我想去旅游', 'sender': '王雷潇', 'time': '2025-03-02 01:53:44'}, {'id': 2, 'content': '好啊，你想去哪里', 'sender': 'me（not ai）', 'time': '2025-03-02 01:54:44'}]]
    print(getPrompt(data,'getMessageReply'))