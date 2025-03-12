import sqlite3
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
        self.tableDefinition = {}
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
            self.tableDefinition = columns  # Save table structure for validation
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
        """设置操作的表名，并验证表是否存在。同时更新表定义。"""
        try:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tableName,))
            if not self.cursor.fetchone():
                raise self.DatabaseControllerException(f"表 {tableName} 不存在")
            self.tableName = tableName
            # 获取表的列定义
            self.cursor.execute(f"PRAGMA table_info({tableName})")
            columns = self.cursor.fetchall()
            self.tableDefinition = {col[1]: col[2] for col in columns}
        except sqlite3.Error as e:
            raise self.DatabaseControllerException(f"设置表名失败：{e}")

    def _checkTableSet(self):
        """检查是否已设置数据表名，未设置则抛出异常。"""
        if not self.tableName:
            raise self.DatabaseControllerException("未设置数据表名，无法执行操作。")

    def _validateData(self, data):
        """验证数据是否符合表的定义。"""
        # 将表定义的列名转换为小写
        lower_table_definition = {col.lower(): col_type for col, col_type in self.tableDefinition.items()}
        for col, value in data.items():
            lower_col = col.lower()
            if lower_col not in lower_table_definition:
                raise self.DatabaseControllerException(f"列 {col} 不在表定义中。")

    
    def selectAllData(self):
        """返回一个 baseData 对象列表，包含表中所有数据。"""
        self._checkTableSet()
        try:
            self.cursor.execute(f"SELECT * FROM {self.tableName}")
            rows = self.cursor.fetchall()
            return [self.baseData(**dict(zip([column[0] for column in self.cursor.description], row))) for row in rows]
        except sqlite3.Error as e:
            raise self.DatabaseControllerException(f"查询所有数据失败：{e}")

    def _buildCondition(self, args):
        """构建条件部分的 SQL 语句。"""
        if not args:
            raise self.DatabaseControllerException("查询条件不能为空。")
        conditions = []
        values = []
        for col, operator, value in args:
            if operator not in ["=", ">", "<", "LIKE"]:
                raise self.DatabaseControllerException(f"不支持的操作符 {operator}。")
            conditions.append(f"{col} {operator} ?")
            values.append(value)
        return " AND ".join(conditions), values

    def selectDataBy(self, *args):
        """根据条件返回一个 baseData 对象列表。"""
        self._checkTableSet()
        try:
            condition, values = self._buildCondition(args)
            query = f"SELECT * FROM {self.tableName} WHERE {condition}"
            self.cursor.execute(query, tuple(values))
            rows = self.cursor.fetchall()
            return [self.baseData(**dict(zip([column[0] for column in self.cursor.description], row))) for row in rows]
        except sqlite3.Error as e:
            raise self.DatabaseControllerException(f"根据条件查询数据失败：{e}")

    def insertData(self, data):
        """接收一个字典对象，将数据插入到数据库中。"""
        self._checkTableSet()
        self._validateData(data)
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
        if not data:
            raise self.DatabaseControllerException("更新数据不能为空。")
        self._validateData(data)
        try:
            set_clause = ", ".join([f"{col} = ?" for col in data])
            condition, values = self._buildCondition(args)
            query = f"UPDATE {self.tableName} SET {set_clause} WHERE {condition}"
            values = list(data.values()) + values
            self.cursor.execute(query, tuple(values))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise self.DatabaseControllerException(f"更新数据失败：{e}")

    def deleteDataBy(self, *args):
        """接收若干个元组，元组格式为（列名，值），根据内容删除数据库中的数据。"""
        self._checkTableSet()
        try:
            condition, values = self._buildCondition(args)
            query = f"DELETE FROM {self.tableName} WHERE {condition}"
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

    def bulkInsertData(self, data_list):
        """批量插入数据。"""
        self._checkTableSet()
        if not data_list:
            raise self.DatabaseControllerException("数据列表不能为空。")
        self._validateData(data_list[0])  # Validate first entry structure
        try:
            columns = ", ".join(data_list[0].keys())
            placeholders = ", ".join(["?" for _ in data_list[0]])
            query = f"INSERT INTO {self.tableName} ({columns}) VALUES ({placeholders})"
            self.cursor.executemany(query, [tuple(data.values()) for data in data_list])
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise self.DatabaseControllerException(f"批量插入数据失败：{e}")

    def bulkUpdateDataBy(self, data_list, *args):
        """批量更新数据。"""
        self._checkTableSet()
        if not data_list:
            raise self.DatabaseControllerException("数据列表不能为空。")
        self._validateData(data_list[0])  # Validate first entry structure
        try:
            set_clause = ", ".join([f"{col} = ?" for col in data_list[0]])
            condition, values = self._buildCondition(args)
            query = f"UPDATE {self.tableName} SET {set_clause} WHERE {condition}"
            self.cursor.executemany(query, [tuple(data.values()) + values for data in data_list])
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise self.DatabaseControllerException(f"批量更新数据失败：{e}")

    def bulkDeleteDataBy(self, *args):
        """批量删除数据。"""
        self._checkTableSet()
        try:
            condition, values = self._buildCondition(args)
            query = f"DELETE FROM {self.tableName} WHERE {condition}"
            self.cursor.executemany(query, [tuple(values)])
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise self.DatabaseControllerException(f"批量删除数据失败：{e}")
        
    def createTableBySettings(self, tableName, data):
        columns = {}
        for column_name, column_info in data.items():
            columns[column_name] = column_info['type']
        self.createTable(tableName, columns)


if __name__ == "__main__":
    import json
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