#!/usr/bin/env python3
"""
数据库迁移脚本：为 students 表添加 quietness 和 cleanliness 字段
"""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from start import app, db

def migrate_database():
    """添加缺失的字段到数据库"""
    with app.app_context():
        # 获取数据库路径
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"正在迁移数据库: {db_path}")
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # 检查 quietness 列是否存在
            cursor.execute("PRAGMA table_info(students)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'quietness' not in columns:
                print("添加 quietness 列...")
                cursor.execute("ALTER TABLE students ADD COLUMN quietness INTEGER")
                print("✅ quietness 列已添加")
            else:
                print("✓ quietness 列已存在")
            
            if 'cleanliness' not in columns:
                print("添加 cleanliness 列...")
                cursor.execute("ALTER TABLE students ADD COLUMN cleanliness INTEGER")
                print("✅ cleanliness 列已添加")
            else:
                print("✓ cleanliness 列已存在")
            
            # 提交更改
            conn.commit()
            print("\n✅ 数据库迁移完成！")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 迁移失败: {e}")
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    migrate_database()
