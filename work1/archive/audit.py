from models.database import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    detail = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')
    
    @staticmethod
    def log_action(user_id, action, detail, ip_address):
        """记录用户操作"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            detail=detail,
            ip_address=ip_address
        )
        db.session.add(log)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e