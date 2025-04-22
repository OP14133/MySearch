# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from datetime import datetime
# # 设置数据库的URL
# SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:111111@localhost/graduation"
#
# # 创建数据库引擎
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL,  # 数据库连接地址
#     # echo=True,                  # 打印SQL语句
#     # connect_args={"check_same_thread": False}    # 解决多线程问题  sqlite使用
# )
#
# # 创建会话
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)
#
# # 映射
# Base = declarative_base()
