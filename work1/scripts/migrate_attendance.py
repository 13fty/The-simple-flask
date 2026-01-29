"""
打卡功能数据库迁移脚本
用于添加打卡记录表和更新现有表结构
"""
from datetime import datetime
import sqlite3
import os

def migrate_attendance():
    """迁移打卡功能相关的数据库表"""
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(basedir, 'dorm_system.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查 attendance_records 表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='attendance_records'
        """)
        
        if cursor.fetchone():
            print("attendance_records 表已存在，检查是否需要更新...")
            
            # 检查是否有 check_in_time 字段
            cursor.execute("PRAGMA table_info(attendance_records)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'check_in_time' not in columns:
                print("添加 check_in_time 字段...")
                # SQLite 不支持非常量默认值，先添加列，然后更新现有记录
                cursor.execute("""
                    ALTER TABLE attendance_records 
                    ADD COLUMN check_in_time DATETIME
                """)
                # 为现有记录设置默认值
                cursor.execute("""
                    UPDATE attendance_records 
                    SET check_in_time = CURRENT_TIMESTAMP 
                    WHERE check_in_time IS NULL
                """)
                print("✓ check_in_time 字段添加成功")
            else:
                print("✓ check_in_time 字段已存在")
            
            # 检查唯一约束
            cursor.execute("PRAGMA index_list(attendance_records)")
            indexes = [idx[1] for idx in cursor.fetchall()]
            
            if 'unique_user_date' not in indexes:
                print("添加唯一约束...")
                # SQLite 不支持直接添加唯一约束，需要重建表
                cursor.execute("""
                    CREATE TABLE attendance_records_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        date DATE NOT NULL,
                        status VARCHAR(20) DEFAULT 'checked_in',
                        check_in_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        UNIQUE(user_id, date)
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO attendance_records_new 
                    (id, user_id, date, status, check_in_time)
                    SELECT id, user_id, date, status, 
                           COALESCE(check_in_time, CURRENT_TIMESTAMP)
                    FROM attendance_records
                """)
                
                cursor.execute("DROP TABLE attendance_records")
                cursor.execute("ALTER TABLE attendance_records_new RENAME TO attendance_records")
                print("✓ 唯一约束添加成功")
            else:
                print("✓ 唯一约束已存在")
        else:
            print("创建 attendance_records 表...")
            cursor.execute("""
                CREATE TABLE attendance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    status VARCHAR(20) DEFAULT 'checked_in',
                    check_in_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, date)
                )
            """)
            print("✓ attendance_records 表创建成功")
        
        conn.commit()
        print("\n✓ 数据库迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ 数据库迁移失败: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("开始执行打卡功能数据库迁移...")
    migrate_attendance()

