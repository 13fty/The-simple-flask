from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config.config import config
from models.database import db
from utils.error_handlers import configure_logging, configure_error_handlers
from models.user import User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'

@login_manager.user_loader
def load_user(user_id):
    """用于 Flask-Login 加载用户"""
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)
    
    # 配置日志和错误处理
    configure_logging(app)
    configure_error_handlers(app)
    
    # 注册蓝图
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.main import main_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # Import models to ensure they are registered with SQLAlchemy
        from models.system import Announcement
        from models.user import User, Student, Major
        from models.dormitory import Building, Dormitory, Bed
        from models.application import SelectionBatch, DormApplication
        
        # Initialize database if empty
        if not User.query.first():
            from datetime import datetime, timedelta
            from werkzeug.security import generate_password_hash
            from models.database import UserRole
            
            # Create admin user
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role=UserRole.ADMIN.value
            )
            db.session.add(admin)
            db.session.commit()
            
            # Create test announcements
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
    
    return app