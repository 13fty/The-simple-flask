from flask import Flask
from models.database import db
from models.user import User, Student, Major
from models.dormitory import Building, Dormitory, Bed
from models.application import SelectionBatch
from models.system import Announcement, DormReview
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from models.database import UserRole, BedStatus, ApplicationStatus

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dorm_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role=UserRole.ADMIN.value
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")

        # Create some test announcements
        if not Announcement.query.first():
            announcements = [
                {
                    'title': '新学期宿舍申请开始',
                    'content': '2025-2026学年宿舍申请现已开放，请同学们及时登录系统进行申请。',
                    'category': '重要通知',
                    'priority': 5,
                    'expire_at': datetime.now() + timedelta(days=30)
                },
                {
                    'title': '宿舍维修通知',
                    'content': '1号楼将于下周进行例行维护，请相关同学配合。',
                    'category': '维护通知',
                    'priority': 3,
                    'expire_at': datetime.now() + timedelta(days=7)
                }
            ]
            
            for ann_data in announcements:
                announcement = Announcement(
                    title=ann_data['title'],
                    content=ann_data['content'],
                    category=ann_data['category'],
                    priority=ann_data['priority'],
                    created_by=admin.id,
                    expire_at=ann_data['expire_at']
                )
                db.session.add(announcement)
            db.session.commit()
            print("Test announcements created successfully")

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully")