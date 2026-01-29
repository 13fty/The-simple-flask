from models.database import db
from datetime import datetime

class VisitorLog(db.Model):
    #从数据库visitor_logs表中获取数据
    __tablename__ = 'visitor_logs'
    id = db.Column(db.Integer, primary_key=True)
    visitor_name = db.Column(db.String(50), nullable=False)
    visitor_id = db.Column(db.String(18), nullable=False)  # 身份证号
    host_student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    visit_date = db.Column(db.Date, nullable=False)
    purpose = db.Column(db.Text)
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    status = db.Column(db.String(20))  #
    
    host_student = db.relationship('Student', backref='visitor_logs')
    
    def check_in(self):
        """访客签到"""
        if self.status != 'approved':
            raise ValueError('访客申请未审批通过')
        self.status = 'checked_in'
        self.check_in_time = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
            
    def check_out(self):
        """访客签出"""
        if self.status != 'checked_in':
            raise ValueError('访客未签到')
        self.status = 'checked_out'
        self.check_out_time = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e