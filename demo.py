import time

# 假设时间戳为 1640995200 （举例）
timestamp = time.time()

# 将时间戳转换为 struct_time 对象
time_struct = time.localtime(timestamp)

# 将 struct_time 对象格式化为指定的字符串格式
formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time_struct)

print(formatted_time)