from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from models.database import db, BedStatus, ApplicationStatus, AttendanceRecord
from models.user import Student, Bed
from models.dormitory import Dormitory, Building
from models.application import DormApplication, SelectionBatch

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    student = current_user.student
    
    # 获取当前住宿信息
    if student.current_bed:
        dorm_info = {
            'building': student.current_bed.dorm.building.name,
            'room': student.current_bed.dorm.room_number,
            'bed': student.current_bed.bed_number,
            'roommates': Student.query.join(Bed).filter(
                Bed.dorm_id == student.current_bed.dorm_id,
                Student.id != student.id
            ).all()
        }
    else:
        dorm_info = None
    
    # 获取申请记录
    applications = DormApplication.query.filter_by(
        student_id=student.id
    ).order_by(DormApplication.created_at.desc()).limit(5).all()
    
    # 获取当前可用的选宿批次
    available_batch = SelectionBatch.query.filter(
        SelectionBatch.is_active == True,
        SelectionBatch.start_time <= datetime.utcnow(),
        SelectionBatch.end_time >= datetime.utcnow()
    ).first()
    
    # 获取最近30天的打卡记录
    start_date = date.today() - timedelta(days=30)
    end_date = date.today()
    
    attendance_records = AttendanceRecord.query.filter(
        AttendanceRecord.user_id == current_user.id,
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    ).all()
    
    # 构建日期到状态的映射
    attendance_dict = {r.date: r.status for r in attendance_records}
    
    # 生成最近30天的日期列表
    attendance_calendar = []
    current = start_date
    while current <= end_date:
        status = attendance_dict.get(current, 'not_checked')
        attendance_calendar.append({
            'date': current,
            'status': status
        })
        current += timedelta(days=1)
    
    return render_template('student/dashboard.html',
                         student=student,
                         dorm_info=dorm_info,
                         applications=applications,
                         available_batch=available_batch,
                         attendance_calendar=attendance_calendar)
