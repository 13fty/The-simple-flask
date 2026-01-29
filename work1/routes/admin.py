from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from models.database import db, UserRole, BedStatus, ApplicationStatus, AttendanceRecord
from models.user import Student, User
from models.dormitory import Dormitory, Building, Bed
from models.application import DormApplication

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != UserRole.ADMIN.value:
        flash('权限不足', 'error')
        return redirect(url_for('main.index'))
    
    # 统计数据
    stats = {
        'total_students': Student.query.count(),
        'total_dorms': Dormitory.query.count(),
        'occupied_beds': Bed.query.filter_by(status=BedStatus.OCCUPIED.value).count(),
        'pending_applications': DormApplication.query.filter_by(
            status=ApplicationStatus.PENDING.value
        ).count()
    }
    
    # 最新申请
    recent_applications = DormApplication.query.order_by(
        DormApplication.created_at.desc()
    ).limit(10).all()
    
    # 获取今日打卡统计
    today = date.today()
    total_students = User.query.filter_by(role=UserRole.STUDENT.value).count()
    checked_in_today = AttendanceRecord.query.filter_by(
        date=today,
        status='checked_in'
    ).count()
    not_checked_today = total_students - checked_in_today
    
    attendance_stats = {
        'total_students': total_students,
        'checked_in': checked_in_today,
        'not_checked': not_checked_today,
        'date': today.isoformat()
    }
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_applications=recent_applications,
                         attendance_stats=attendance_stats)

@admin_bp.route('/application/<int:app_id>/process', methods=['POST'])
@login_required
def process_application(app_id):
    if current_user.role not in [UserRole.ADMIN.value, UserRole.DORM_MANAGER.value]:
        flash('权限不足', 'error')
        return redirect(url_for('main.index'))
    
    application = DormApplication.query.get_or_404(app_id)
    action = request.form['action']
    remarks = request.form.get('remarks', '')
    
    if action == 'approve':
        # 检查申请状态
        if application.status != ApplicationStatus.PENDING.value:
            flash('该申请已被处理', 'error')
            return redirect(request.referrer or url_for('admin.dashboard'))
        
        student = application.student
        
        # 处理换宿申请
        if application.application_type == 'change':
            # 检查目标床位是否仍然可用
            target_bed = application.bed
            if target_bed.status != BedStatus.RESERVED.value:
                flash('目标床位状态已变更，无法批准申请', 'error')
                return redirect(request.referrer or url_for('admin.dashboard'))
            
            # 释放原床位
            if student.current_bed:
                old_bed = student.current_bed
                old_bed.status = BedStatus.AVAILABLE.value
            
            # 分配新床位
            target_bed.status = BedStatus.OCCUPIED.value
            student.current_bed_id = target_bed.id
            
            application.status = ApplicationStatus.APPROVED.value
            flash('换宿申请已批准', 'success')
        
        # 处理新申请（选宿）
        elif application.application_type == 'new':
            # 检查学生是否已有床位
            if student.current_bed_id:
                flash('该学生已有床位，无法批准新申请', 'error')
                # 释放预留的床位
                if application.bed.status == BedStatus.RESERVED.value:
                    application.bed.status = BedStatus.AVAILABLE.value
                return redirect(request.referrer or url_for('admin.dashboard'))
            
            # 分配床位
            bed = application.bed
            bed.status = BedStatus.OCCUPIED.value
            student.current_bed_id = bed.id
            
            application.status = ApplicationStatus.APPROVED.value
            flash('选宿申请已批准', 'success')
        
        else:
            flash('未知的申请类型', 'error')
            return redirect(request.referrer or url_for('admin.dashboard'))
        
    elif action == 'reject':
        if application.status != ApplicationStatus.PENDING.value:
            flash('该申请已被处理', 'error')
            return redirect(request.referrer or url_for('admin.dashboard'))
        
        application.status = ApplicationStatus.REJECTED.value
        # 释放预留的床位
        if application.bed and application.bed.status == BedStatus.RESERVED.value:
            application.bed.status = BedStatus.AVAILABLE.value
        
        if application.application_type == 'change':
            flash('换宿申请已拒绝', 'info')
        else:
            flash('申请已拒绝', 'info')
    
    try:
        application.processed_at = datetime.utcnow()
        application.processed_by = current_user.id
        application.remarks = remarks
        
        db.session.commit()
        return redirect(request.referrer or url_for('admin.dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'处理申请时发生错误：{str(e)}', 'error')
        return redirect(request.referrer or url_for('admin.dashboard'))
