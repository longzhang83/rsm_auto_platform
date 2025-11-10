"""
数据库初始化脚本
"""
from app.db.database import engine, Base
from app.db import models  # 导入models

print("正在初始化数据库...")
Base.metadata.create_all(bind=engine)
print("数据库初始化完成!")
print(f"数据库文件: rsm_auto_platform.db")
print(f"创建的表: {', '.join(Base.metadata.tables.keys())}")
