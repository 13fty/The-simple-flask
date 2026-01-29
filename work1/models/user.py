from flask_login import UserMixin
from .database import db, UserRole

class User(UserMixin, db.Model):
#从数据库users表中获取数据
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default=UserRole.STUDENT.value)
    student = db.relationship('Student', backref='user', uselist=False)

class Major(db.Model):
    __tablename__ = 'majors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    department = db.Column(db.String(50))

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(10), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(50), nullable=False)
    id_card = db.Column(db.String(18), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    major_id = db.Column(db.Integer, db.ForeignKey('majors.id'))
    grade = db.Column(db.Integer)  # 年级
    
    # 生活习惯偏好
    sleep_time = db.Column(db.String(20))  # 早睡/晚睡
    wake_time = db.Column(db.String(20))   # 早起/晚起
    quietness = db.Column(db.Integer)      # 安静程度 1-5
    cleanliness = db.Column(db.Integer)    # 清洁程度 1-5
    hobbies = db.Column(db.Text)
    
    # 宿舍相关
    current_bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('dorm_teams.id'))
    
    major = db.relationship('Major', backref='students')
    current_bed = db.relationship('Bed', foreign_keys=[current_bed_id], backref='current_student')
