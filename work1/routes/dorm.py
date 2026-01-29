from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.database import db, BedStatus, ApplicationStatus
from models.dormitory import Dormitory, Building, Bed
from models.user import Student
from models.application import DormApplication

dorm_bp = Blueprint('dorm', __name__)

@dorm_bp.route('/browse')
def browse():
    # 获取筛选参数
    building_id = request.args.get('building_id', type=int)
    capacity = request.args.get('capacity', type=int)
    floor = request.args.get('floor', type=int)
    gender = request.args.get('gender')
    
    # 构建查询
    query = Dormitory.query.join(Building)
    
    # 基础筛选
    if building_id:
        query = query.filter(Dormitory.building_id == building_id)
    if capacity:
        query = query.filter(Dormitory.capacity == capacity)
    if floor:
        query = query.filter(Dormitory.floor == floor)
    if gender:
        query = query.filter(Building.gender == gender)
    
    # 分页
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=12)
    
    # 获取楼栋列表用于筛选
    buildings = Building.query.all()
    
    return render_template('dorms/browse.html',
                         dorms=pagination.items,
                         pagination=pagination,
                         buildings=buildings)

@dorm_bp.route('/<int:dorm_id>')
def detail(dorm_id):
    dorm = Dormitory.query.get_or_404(dorm_id)
    
    # 获取评价统计
    from models.system import DormReview
    reviews = DormReview.query.filter_by(dorm_id=dorm_id).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
    
    # 获取床位状态
    beds_status = {
        'available': len([b for b in dorm.beds if b.status == BedStatus.AVAILABLE.value]),
        'occupied': len([b for b in dorm.beds if b.status == BedStatus.OCCUPIED.value]),
        'reserved': len([b for b in dorm.beds if b.status == BedStatus.RESERVED.value])
    }
    
    return render_template('dorms/detail.html',
                         dorm=dorm,
                         reviews=reviews[:5],  # 显示最新5条评价
                         avg_rating=avg_rating,
                         beds_status=beds_status)

@dorm_bp.route('/<int:dorm_id>/select', methods=['POST'])
@login_required
def select(dorm_id):
    student = current_user.student
    bed_id = request.form.get('bed_id', type=int)
    
    # 检查是否在选宿时间内
    from models.application import SelectionBatch
    current_batch = SelectionBatch.query.filter(
        SelectionBatch.is_active == True,
        SelectionBatch.start_time <= datetime.utcnow(),
        SelectionBatch.end_time >= datetime.utcnow()
    ).first()
    
    if not current_batch:
        flash('当前不在选宿时间内', 'error')
        return redirect(url_for('dorm.detail', dorm_id=dorm_id))
    
    # 检查床位状态
    bed = Bed.query.get_or_404(bed_id)
    if bed.status != BedStatus.AVAILABLE.value:
        flash('该床位已被占用', 'error')
        return redirect(url_for('dorm.detail', dorm_id=dorm_id))
    
    # 创建申请
    application = DormApplication(
        #学生申请换宿，床位id，申请类型，状态
        student_id=student.id,
        bed_id=bed_id,
        application_type='new',
        status=ApplicationStatus.PENDING.value
    )
    
    try:
        # 检查学生是否已有床位
        if student.current_bed_id:
            flash('您已有床位，请先退宿后再申请', 'error')
            return redirect(url_for('dorm.detail', dorm_id=dorm_id))
        
        # 更新床位状态为预留
        bed.status = BedStatus.RESERVED.value
        
        db.session.add(application)
        db.session.commit()
        
        flash('选宿申请已提交，请等待审核', 'success')
        return redirect(url_for('student_dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'提交申请时发生错误：{str(e)}', 'error')
        return redirect(url_for('dorm.detail', dorm_id=dorm_id))
