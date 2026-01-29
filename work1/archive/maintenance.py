from models.database import db
from datetime import datetime

class MaintenanceRequest(db.Model):
    __tablename__ = 'maintenance_requests'
    id = db.Column(db.Integer, primary_key=True)
    dorm_id = db.Column(db.Integer, db.ForeignKey('dormitories.id'))
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    issue_type = db.Column(db.String(50))  # 维修类型：水电/家具/其他
    description = db.Column(db.Text)
    status = db.Column(db.String(20))  # pending/in_progress/completed/cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    dorm = db.relationship('Dormitory', backref='maintenance_requests')
    reporter = db.relationship('User', backref='reported_maintenance')
    
    def update_status(self, new_status):
        """更新维修状态"""
        self.status = new_status
        if new_status == 'completed':
            self.completed_at = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e