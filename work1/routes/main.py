from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models.user import UserRole

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # 获取最新公告
    from models.system import Announcement
    from datetime import datetime
    
    announcements = Announcement.query.filter(
        Announcement.expire_at > datetime.utcnow()
    ).order_by(Announcement.priority.desc(), Announcement.created_at.desc()).limit(5).all()
    
    # 获取当前选宿批次
    from models.application import SelectionBatch
    current_batch = SelectionBatch.query.filter(
        SelectionBatch.is_active == True,
        SelectionBatch.start_time <= datetime.utcnow(),
        SelectionBatch.end_time >= datetime.utcnow()
    ).first()
    
    return render_template('index.html', 
                         announcements=announcements,
                         current_batch=current_batch)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == UserRole.ADMIN.value:
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == UserRole.DORM_MANAGER.value:
        return redirect(url_for('manager.dashboard'))
    else:
        return redirect(url_for('student_dashboard'))
