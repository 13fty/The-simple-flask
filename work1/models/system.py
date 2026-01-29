from datetime import datetime
from .database import db

class DormReview(db.Model):
    """宿舍评价"""
    __tablename__ = 'dorm_reviews'
    id = db.Column(db.Integer, primary_key=True)
    dorm_id = db.Column(db.Integer, db.ForeignKey('dormitories.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    
    rating = db.Column(db.Integer)  # 1-5星
    environment_rating = db.Column(db.Integer)
    facilities_rating = db.Column(db.Integer)
    location_rating = db.Column(db.Integer)
    
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    dorm = db.relationship('Dormitory', backref='reviews')
    student = db.relationship('Student', backref='reviews')

class Announcement(db.Model):
    """公告通知"""
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # 通知类型
    priority = db.Column(db.Integer, default=0)  # 优先级
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expire_at = db.Column(db.DateTime)
    
    author = db.relationship('User', backref='announcements')

