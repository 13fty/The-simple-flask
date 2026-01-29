from models.database import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    type = db.Column(db.String(20))  # system/application/maintenance
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')
    
    @staticmethod
    def create_notification(user_id, title, content, type='system'):
        """创建通知"""
        notification = Notification(
            user_id=user_id,
            title=title,
            content=content,
            type=type
        )
        db.session.add(notification)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
            
    def mark_as_read(self):
        """标记通知为已读"""
        self.is_read = True
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e