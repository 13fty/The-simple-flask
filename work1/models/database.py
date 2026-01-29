from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

# 枚举类型
class UserRole(Enum):
    STUDENT = 'student'
    ADMIN = 'admin'
    DORM_MANAGER = 'dorm_manager'

class BedStatus(Enum):
    AVAILABLE = 'available'
    OCCUPIED = 'occupied'
    RESERVED = 'reserved'
    MAINTENANCE = 'maintenance'

class ApplicationStatus(Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='checked_in')  # 状态：checked_in（已打卡）/not_checked（未打卡）
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)  # 打卡时间

    user = db.relationship('User', backref='attendance_records')
    
    # 添加唯一约束，确保每个用户每天只有一条记录
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)

    def __repr__(self):
        return f"<AttendanceRecord user_id={self.user_id} date={self.date} status={self.status}>"
