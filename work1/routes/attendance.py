from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from models.database import db, AttendanceRecord
from models.user import User, Student

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/check_in', methods=['POST'])
@login_required
def check_in():
    """用户打卡接口"""
    today = date.today()
    
    # 检查今天是否已经打卡
    existing_record = AttendanceRecord.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    if existing_record:
        if existing_record.status == 'checked_in':
            return jsonify({
                'success': False,
                'message': '今天已经打卡过了！'
            }), 400
        else:
            # 如果之前是未打卡状态，更新为已打卡
            existing_record.status = 'checked_in'
            existing_record.check_in_time = datetime.utcnow()
    else:
        # 创建新的打卡记录
        new_record = AttendanceRecord(
            user_id=current_user.id,
            date=today,
            status='checked_in',
            check_in_time=datetime.utcnow()
        )
        db.session.add(new_record)
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '打卡成功！'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'打卡失败：{str(e)}'
        }), 500

@attendance_bp.route('/check_today', methods=['GET'])
@login_required
def check_today():
    """检查今天是否已打卡"""
    today = date.today()
    record = AttendanceRecord.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    if record and record.status == 'checked_in':
        return jsonify({
            'checked': True,
            'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None
        }), 200
    else:
        return jsonify({
            'checked': False
        }), 200

@attendance_bp.route('/records', methods=['GET'])
@login_required
def get_records():
    """获取用户的打卡记录（用于日程表）"""
    # 获取最近30天的记录
    start_date = date.today() - timedelta(days=30)
    end_date = date.today()
    
    records = AttendanceRecord.query.filter(
        AttendanceRecord.user_id == current_user.id,
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    ).all()
    
    # 构建日期到状态的映射
    record_dict = {r.date: r.status for r in records}
    
    # 生成最近30天的日期列表
    date_list = []
    current = start_date
    while current <= end_date:
        status = record_dict.get(current, 'not_checked')
        date_list.append({
            'date': current.isoformat(),
            'status': status
        })
        current += timedelta(days=1)
    
    return jsonify({
        'success': True,
        'records': date_list
    }), 200

@attendance_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """获取打卡统计（管理员使用）"""
    # 检查是否为管理员
    if current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    # 获取查询日期，默认为今天
    query_date_str = request.args.get('date', date.today().isoformat())
    try:
        query_date = datetime.strptime(query_date_str, '%Y-%m-%d').date()
    except:
        query_date = date.today()
    
    # 获取所有学生用户
    students = User.query.filter_by(role='student').all()
    total_students = len(students)
    
    # 获取该日期的打卡记录
    checked_records = AttendanceRecord.query.filter_by(
        date=query_date,
        status='checked_in'
    ).count()
    
    not_checked = total_students - checked_records
    
    return jsonify({
        'success': True,
        'date': query_date.isoformat(),
        'total_students': total_students,
        'checked_in': checked_records,
        'not_checked': not_checked
    }), 200

