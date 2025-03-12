import json
from wxauto import WeChat
from databaseController import DatabaseController

    
def initFriendsInfo(settings,databaseController):
    wx = WeChat()
    friend_details = wx.GetFriendDetails(timeout=settings["friendsListSearchTime"])
    for item in friend_details:
        data = {
            "real_name": item.get('实名', None),
            "nick_name": item.get('昵称', None),
            "wechat_id": item.get('微信号', None),
            "location": item.get('地区', None),
            "remark": item.get('备注', None),
            "signature": item.get('个性签名', None),
            "source": item.get('来源', None),
            "gender": None,
            "relation": None,
            "relationship_strength": None,
            "lunar_birthday": None,
            "gregorian_birthday": None,
            "constellation": None,
            "hometown": None,
            "hobbies": None,
            "commitments": None,
            "personality": None,
            "graduation_school": None,
            "company": item.get('企业', None),
            "position": None,
            "other_info": None
        }


        databaseController.setTableName(settings["databaseTables"][0])
        databaseController.insertData(data)
       

    # 提交更改
    

def init():
    with open('setting.json', 'r', encoding='utf-8') as file:
        settings = json.load(file)
    if not settings["isInit"]:
        databaseController = DatabaseController(settings["databaseName"])

        # 遍历数据库表定义
        for table_name, columns_info in settings["databaseTablesDef"].items():
            # 提取列名和列类型
            columns = {col: info["type"] for col, info in columns_info.items()}
            try:
                # 创建表
                databaseController.createTable(table_name, columns)
                print(f"成功创建表 {table_name}")
            except databaseController.DatabaseControllerException as e:
                print(f"创建表 {table_name} 失败: {e}")
        initFriendsInfo(settings,databaseController)
        print("系统初始化成功！")
        databaseController.close()
        settings["isInit"] = True
        with open('setting.json', 'w', encoding='utf-8') as setting:
            json.dump(settings, setting, ensure_ascii=False, indent=4)

if __name__ == '__main__':



    with open('setting.json', 'r', encoding='utf-8') as file:
        settings = json.load(file)
    print(settings["databaseTables"][0])
    init()