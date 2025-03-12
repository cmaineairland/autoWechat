import sqlite3
import json
import re


class DatabaseController:

    class DatabaseControllerException(Exception):
        """自定义异常类，用于处理数据库控制器相关的错误。"""
        def __init__(self, message):
            self.message = message

        def __str__(self):
            return self.message

    class baseData:
        """表中一行的数据对象化"""
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def __init__(self, databaseName):
        """初始化数据库控制器，连接到指定的数据库。"""
        self.databaseName = databaseName
        self.conn = None
        self.cursor = None
        self.tableName = None
        self._connect()

    def __str__(self):
        return f"DatabaseController(databaseName={self.databaseName}, tableName={self.tableName})"

    def __enter__(self):
        return self

    def _connect(self):
        """建立数据库连接，并创建游标。"""
        try:
            self.conn = sqlite3.connect(self.databaseName)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            raise self.DatabaseControllerException(f"连接数据库失败：{e}")

    def createTable(self, tableName, columns):
        """创建一个表，并验证表名是否合法。columns是一个字典，键为列名，值为列类型。"""
        # 验证表名是否合法
        if not re.match(r'^[a-zA-Z0-9_]+$', tableName):
            raise self.DatabaseControllerException(f"表名 {tableName} 不合法，表名只能包含字母、数字和下划线。")
        try:
            # 构建列定义部分
            column_definitions = ", ".join([f"{col} {col_type}" for col, col_type in columns.items()])
            # 构建创建表的 SQL 语句
            query = f"CREATE TABLE IF NOT EXISTS {tableName} ({column_definitions})"
            # 执行 SQL 语句
            self.cursor.execute(query)
            self.conn.commit()
            self.setTableName(tableName)

        except sqlite3.Error as e:
            self.conn.rollback()
            raise self.DatabaseControllerException(f"创建表 {tableName} 失败：{e}")


    def deleteTable(self, tableName):
        """删除一个表，并验证表是否存在。"""
        try:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tableName,))
            if not self.cursor.fetchone():
                raise self.DatabaseControllerException(f"表 {tableName} 不存在。")
            self.cursor.execute(f"DROP TABLE {tableName}")
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise self.DatabaseControllerException(f"删除表 {tableName} 失败：{e}")

    def setTableName(self, tableName):
        """设置操作的表名，并验证表是否存在。"""
        try:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tableName,))
            if not self.cursor.fetchone():
                raise self.DatabaseControllerException(f"表 {tableName} 不存在")
            self.tableName = tableName
        except sqlite3.Error as e:
            raise self.DatabaseControllerException(f"设置表名失败：{e}")

    def _checkTableSet(self):
        """检查是否已设置数据表名，未设置则抛出异常。"""
        if not self.tableName:
            raise self.DatabaseControllerException("未设置数据表名，无法执行操作。")

    def selectAllData(self):
        """返回一个 baseData 对象列表，包含表中所有数据。"""
        self._checkTableSet()
        try:
            self.cursor.execute(f"SELECT * FROM {self.tableName}")
            rows = self.cursor.fetchall()
            return [self.baseData(**dict(zip([column[0] for column in self.cursor.description], row))) for row in rows]
        except sqlite3.Error as e:
            raise self.DatabaseControllerException(f"查询所有数据失败：{e}")

    def selectDataBy(self, *args):
        """根据条件返回一个 baseData 对象列表。"""
        self._checkTableSet()
        try:
            where_clause = " AND ".join([f"{col} = ?" for col, _ in args])
            query = f"SELECT * FROM {self.tableName} WHERE {where_clause}"
            values = [value for _, value in args]
            self.cursor.execute(query, tuple(values))
            rows = self.cursor.fetchall()
            return [self.baseData(**dict(zip([column[0] for column in self.cursor.description], row))) for row in rows]
        except sqlite3.Error as e:
            raise self.DatabaseControllerException(f"根据条件查询数据失败：{e}")

    def insertData(self, data):
        """接收一个字典对象，将数据插入到数据库中。"""
        self._checkTableSet()
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            query = f"INSERT INTO {self.tableName} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, tuple(data.values()))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise self.DatabaseControllerException(f"插入数据失败：{e}")

    def updateDataBy(self, data, *args):
        """接收一个字典对象，若干个元组，元组格式为（列名，值），根据内容更新数据库中的数据。"""
        self._checkTableSet()
        try:
            set_clause = ", ".join([f"{col} = ?" for col in data])
            where_clause = " AND ".join([f"{col} = ?" for col, _ in args])
            query = f"UPDATE {self.tableName} SET {set_clause} WHERE {where_clause}"
            values = list(data.values()) + [value for _, value in args]
            self.cursor.execute(query, tuple(values))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise self.DatabaseControllerException(f"更新数据失败：{e}")

    def deleteDataBy(self, *args):
        """接收若干个元组，元组格式为（列名，值），根据内容删除数据库中的数据。"""
        self._checkTableSet()
        try:
            where_clause = " AND ".join([f"{col} = ?" for col, _ in args])
            query = f"DELETE FROM {self.tableName} WHERE {where_clause}"
            values = [value for _, value in args]
            self.cursor.execute(query, tuple(values))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise self.DatabaseControllerException(f"删除数据失败：{e}")

    def close(self):
        """关闭数据库连接。"""
        if self.conn:
            self.conn.close()
    
    def __exit__(self):
        self.close()



with open('setting.json', 'r', encoding='utf-8') as file:
    settings = json.load(file)
    defaultDatabase = settings['databaseName']

def createDatabase(databaseName=defaultDatabase):
    conn = sqlite3.connect(databaseName)
    conn.close()

def createTable(tables,databaseName=defaultDatabase):
    # 连接到数据库
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    try:
        # 遍历每个表
        for table_name, columns in tables.items():
            # 构建创建表的 SQL 语句
            column_definitions = []
            for column_name, column_info in columns.items():
                column_type = column_info["type"]
                column_definitions.append(f"{column_name} {column_type}")

            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_definitions)});"

            # 执行 SQL 语句
            cursor.execute(sql)

        # 提交事务
        conn.commit()
        print("表创建成功！")
    except Exception as e:
        print(f"表创建失败：{e}")
        # 回滚事务
        conn.rollback()
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()

def insertData(tableName, data,databaseName=defaultDatabase):
    data = json.loads(data)
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect(databaseName)
        cursor = conn.cursor()

        # 构建插入语句
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {tableName} ({columns}) VALUES ({placeholders})"

        # 执行插入操作
        cursor.execute(sql, tuple(data.values()))

        # 提交事务
        conn.commit()
    except sqlite3.Error as e:
        print(f"插入数据时发生错误: {e}")
    finally:
        # 关闭连接
        if conn:
            conn.close()

def getAllData(tableName, databaseName=defaultDatabase):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    # 对表名进行转义处理
    escaped_table_name = f'"{tableName}"'

    # 执行查询语句
    cursor.execute(f"SELECT * FROM {escaped_table_name}")

    # 获取所有行
    rows = cursor.fetchall()

    # 关闭连接
    conn.close()
    return rows

if __name__ == "__main__":
    friendInfoDatabaseController = DatabaseController("AiAgent4WeChat.db")
    friendInfoDatabaseController.setTableName("friendInfo")