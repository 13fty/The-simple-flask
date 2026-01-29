from datetime import datetime
from .database import db, ApplicationStatus

class DormTeam(db.Model):
    """宿舍团队，用于室友组团选宿舍"""
    __tablename__ = 'dorm_teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    max_size = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invite_code = db.Column(db.String(20), unique=True)
    
    leader = db.relationship('Student', foreign_keys=[leader_id])
    members = db.relationship('Student', backref='team', foreign_keys='Student.team_id')

class DormApplication(db.Model):
    """宿舍申请记录"""
    __tablename__ = 'dorm_applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('dorm_teams.id'))
    target_dorm_id = db.Column(db.Integer, db.ForeignKey('dormitories.id'))
    
    application_type = db.Column(db.String(20))  # 'new'/'change'/'cancel'
    status = db.Column(db.String(20), default=ApplicationStatus.PENDING.value)
    reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    remarks = db.Column(db.Text)
    
    student = db.relationship('Student', backref='applications')
    bed = db.relationship('Bed', backref='applications')
    processor = db.relationship('User', backref='processed_applications')

class SelectionBatch(db.Model):
    """选宿批次管理"""
    __tablename__ = 'selection_batches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Integer)  # 适用年级
    major_ids = db.Column(db.Text)  # 适用专业ID列表(JSON)
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    max_applications = db.Column(db.Integer, default=1)  # 每人最大申请数
    description = db.Column(db.Text)
