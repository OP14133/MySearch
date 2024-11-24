import chardet

# 假设乱码数据
bytes_data = "æ°æµªé¦é¡µ ç¸å ³æ°é» æ¹çè°æ¥ è¿åé¡¶é"

# 使用 chardet 自动检测编码
result = chardet.detect(bytes_data)
encoding = result['encoding']

# 使用检测到的编码解码数据
decoded_data = bytes_data.decode(encoding)
print(decoded_data)