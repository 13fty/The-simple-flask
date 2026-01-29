from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from datetime import datetime, timedelta, date
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from enum import Enum
from routes.dorm import dorm_bp
from routes.main import main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.attendance import attendance_bp
# 导入统一的db实例和枚举
from models.database import db, UserRole, BedStatus, ApplicationStatus
# 导入所有模型
from models.user import User, Student, Major
from models.dormitory import Building, Dormitory, Bed
from models.application import DormTeam, DormApplication, SelectionBatch
from models.system import DormReview, Announcement
from models.database import AttendanceRecord

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'your_secret_key_change_in_production'

# 数据库配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'dorm_system.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 初始化db到app
db.init_app(app)

# Flask-Login 配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'

# 注册蓝图
app.register_blueprint(dorm_bp, url_prefix='/dorm')
app.register_blueprint(main_bp, url_prefix='/')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(attendance_bp, url_prefix='/attendance')

# 注意：Message模型暂未在models目录中定义，如果使用请添加到models/system.py
# 暂时在这里定义Message模型（应该移到models/system.py）
class Message(db.Model):
    """学生之间的消息"""
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('Student', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('Student', foreign_keys=[receiver_id], backref='received_messages')

# Flask-Login 用户加载
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def auto_assign_dorm(student, preferred_capacity=None):
    """
    使用贪心算法自动分配宿舍
    优先级：性别匹配 > 宿舍人数偏好 > 专业匹配 > 生活习惯匹配 > 随机分配
    支持向下兼容：4人间满则选6人间，6人间满则选8人间
    """
    # 1. 获取所有可用床位
    available_beds = Bed.query.filter_by(status=BedStatus.AVAILABLE.value).all()
    
    if not available_beds:
        return None
    
    # 2. 按性别筛选可用床位
    gender_matched_beds = []
    for bed in available_beds:
        if bed.dorm.building.gender == student.gender:
            gender_matched_beds.append(bed)
    
    if not gender_matched_beds:
        return None
    
    # 3. 按宿舍人数偏好筛选（支持向下兼容）
    if preferred_capacity:
        # 定义向下兼容的宿舍人数顺序（最多6人间）
        capacity_order = [preferred_capacity]
        if preferred_capacity == 4:
            capacity_order.extend([6])  # 4人间满则选6人间
        elif preferred_capacity == 6:
            capacity_order.extend([4])  # 6人间满则选4人间
        else:
            capacity_order.extend([4, 6])  # 其他情况按常规顺序
        
        # 按偏好顺序筛选可用床位
        preferred_beds = []
        for capacity in capacity_order:
            for bed in gender_matched_beds:
                if bed.dorm.capacity == capacity:
                    preferred_beds.append(bed)
            if preferred_beds:  # 找到可用床位就停止
                break
        
        if not preferred_beds:
            # 如果所有偏好宿舍都满了，使用所有可用床位
            preferred_beds = gender_matched_beds
    else:
        # 没有偏好，使用所有可用床位
        preferred_beds = gender_matched_beds
    
    # 4. 计算每个床位的匹配分数
    bed_scores = []
    for bed in preferred_beds:
        score = 0
        dorm = bed.dorm
        
        # 获取当前宿舍的入住学生
        current_students = []
        for other_bed in dorm.beds:
            if other_bed.status == BedStatus.OCCUPIED.value:
                other_student = Student.query.filter_by(current_bed_id=other_bed.id).first()
                if other_student:
                    current_students.append(other_student)
        
        # 专业匹配分数 (30分)
        if student.major_id:
            same_major_count = 0
            for other in current_students:
                if other.major_id == student.major_id:
                    same_major_count += 1
            score += min(same_major_count * 10, 30)  # 最多30分
        
        # 生活习惯匹配分数 (40分)
        if student.sleep_time and student.wake_time:
            lifestyle_score = 0
            for other in current_students:
                # 作息时间匹配
                if other.sleep_time == student.sleep_time:
                    lifestyle_score += 10
                if other.wake_time == student.wake_time:
                    lifestyle_score += 10
                # 安静程度匹配
                if other.quietness and student.quietness:
                    lifestyle_score += max(0, 10 - abs(other.quietness - student.quietness) * 2)
                # 整洁程度匹配
                if other.cleanliness and student.cleanliness:
                    lifestyle_score += max(0, 10 - abs(other.cleanliness - student.cleanliness) * 2)
            score += min(lifestyle_score, 40)  # 最多40分
        
        # 宿舍偏好分数 (30分)
        # 根据用户偏好和实际宿舍人数计算分数
        if preferred_capacity:
            if dorm.capacity == preferred_capacity:
                score += 30  # 完全匹配偏好
            elif preferred_capacity == 4 and dorm.capacity == 6:
                score += 20  # 4人间满，分配6人间
            elif preferred_capacity == 6 and dorm.capacity == 4:
                score += 20  # 6人间满，分配4人间
            else:
                score += 10  # 其他情况
        else:
            # 没有偏好时的默认分数
            if dorm.capacity == 4:
                score += 20
            elif dorm.capacity == 6:
                score += 15
            else:
                score += 5
        
        # 楼层偏好 (10分)
        # 优先分配中间楼层 (3-7楼)
        if 3 <= dorm.floor <= 7:
            score += 10
        elif dorm.floor in [2, 8]:
            score += 5
        
        # 设施偏好 (10分)
        if dorm.has_ac:
            score += 3
        if dorm.has_bathroom:
            score += 3
        if dorm.has_balcony:
            score += 2
        if dorm.has_water_heater:
            score += 2
        
        bed_scores.append((bed, score))
    
    # 4. 按分数排序，选择最高分的床位
    bed_scores.sort(key=lambda x: x[1], reverse=True)
    
    if bed_scores:
        return bed_scores[0][0]  # 返回分数最高的床位
    
    return None

# 路由部分
@app.route('/')
def index():
    # 获取最新公告
    announcements = Announcement.query.filter(
        Announcement.expire_at > datetime.utcnow()
    ).order_by(Announcement.priority.desc(), Announcement.created_at.desc()).limit(5).all()
    
    # 获取当前选宿批次
    current_batch = SelectionBatch.query.filter(
        SelectionBatch.is_active == True,
        SelectionBatch.start_time <= datetime.utcnow(),
        SelectionBatch.end_time >= datetime.utcnow()
    ).first()
    
    return render_template('index.html', 
                         announcements=announcements,
                         current_batch=current_batch)

@app.route('/register', methods=['GET', 'POST'])
#接收表单信息
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        student_id = request.form['student_id']
        id_card = request.form['id_card']
        gender = request.form['gender']
        major_id = request.form['major_id']
        phone = request.form['phone']
        email = request.form['email']
        
        # 生活习惯信息
        sleep_time = request.form.get('sleep_time')
        wake_time = request.form.get('wake_time')
        hobbies = request.form.get('hobbies')
        
        # 宿舍偏好信息
        preferred_capacity = request.form.get('preferred_capacity', type=int)
        
        # 检查用户名是否存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('register'))
        
        # 创建用户
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=UserRole.STUDENT.value
        )
        db.session.add(user)
        db.session.flush()
        
        # 创建学生信息
        student = Student(
            user_id=user.id,
            student_id=student_id,
            name=name,
            id_card=id_card,
            gender=gender,
            major_id=major_id,
            phone=phone,
            email=email,
            grade=datetime.now().year,
            sleep_time=sleep_time,
            wake_time=wake_time,
            hobbies=hobbies
        )
        db.session.add(student)
        db.session.flush()  # 获取student.id
        
        # 自动分配宿舍
        assigned_bed = auto_assign_dorm(student, preferred_capacity)
        if assigned_bed:
            student.current_bed_id = assigned_bed.id
            assigned_bed.status = BedStatus.OCCUPIED.value
            flash(f'注册成功，宿舍已自动分配（{assigned_bed.dorm.capacity}人间），请登录', 'success')
        else:
            flash('注册成功，但暂无可用宿舍，请稍后联系管理员', 'warning')
        
        db.session.commit()
        return redirect(url_for('login'))
    
    # 如果数据库中没有楼栋数据，先创建10栋宿舍楼
    if Building.query.count() == 0:
        buildings_data = [
            {'name': '1号宿舍楼', 'gender': '男', 'total_floors': 10, 'location': '校园东区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
            {'name': '2号宿舍楼', 'gender': '女', 'total_floors': 10, 'location': '校园东区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
            {'name': '3号宿舍楼', 'gender': '男', 'total_floors': 10, 'location': '校园西区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
            {'name': '4号宿舍楼', 'gender': '女', 'total_floors': 10, 'location': '校园西区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
            {'name': '5号宿舍楼', 'gender': '男', 'total_floors': 10, 'location': '校园南区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
            {'name': '6号宿舍楼', 'gender': '女', 'total_floors': 10, 'location': '校园南区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
            {'name': '7号宿舍楼', 'gender': '男', 'total_floors': 10, 'location': '校园北区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
            {'name': '8号宿舍楼', 'gender': '女', 'total_floors': 10, 'location': '校园北区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
            {'name': '9号宿舍楼', 'gender': '男', 'total_floors': 10, 'location': '校园中心区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
            {'name': '10号宿舍楼', 'gender': '女', 'total_floors': 10, 'location': '校园中心区', 'facilities': '24小时热水、WiFi覆盖、门禁系统、电梯', 'description': '现代化学生宿舍，设施齐全，环境优美'},
        ]
        
        for building_data in buildings_data:
            building = Building(**building_data)
            db.session.add(building)
        db.session.commit()
        
        # 为每栋楼创建宿舍房间
        buildings = Building.query.all()
        for building in buildings:
            for floor in range(1, building.total_floors + 1):
                # 每层创建25个房间（1-25号）
                for room_num in range(1, 26):
                    room_number = f"{floor:02d}{room_num:02d}"
                    
                    # 随机分配4人间或6人间
                    import random
                    capacity = random.choice([4, 6])
                    
                    dorm = Dormitory(
                        building_id=building.id,
                        room_number=room_number,
                        floor=floor,
                        capacity=capacity,
                        room_type='标准间',
                        has_ac=True,
                        has_bathroom=True,
                        has_balcony=floor >= 3,
                        has_water_heater=True,
                        monthly_rent=800.0 if capacity == 4 else 600.0,  # 4人间贵一些
                        area=20.0 if capacity == 4 else 25.0,
                        orientation='南向' if room_num % 2 == 0 else '北向'
                    )
                    db.session.add(dorm)
        
        db.session.commit()
        
        # 为每个宿舍创建床位
        dorms = Dormitory.query.all()
        for dorm in dorms:
            for bed_num in range(1, dorm.capacity + 1):
                position = '上铺' if bed_num % 2 == 0 else '下铺'
                bed = Bed(
                    dorm_id=dorm.id,
                    bed_number=bed_num,
                    position=position,
                    status=BedStatus.AVAILABLE.value
                )
                db.session.add(bed)
        
        db.session.commit()
    
    # 创建管理员账号
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role=UserRole.ADMIN.value
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ 管理员账号已创建：admin / admin123")
    
    # 如果数据库中没有专业数据，先创建一些基础专业
    if Major.query.count() == 0:
        majors_data = [
            {'name': '计算机科学与技术', 'code': 'CS001', 'department': '计算机学院'},
            {'name': '软件工程', 'code': 'SE001', 'department': '计算机学院'},
            {'name': '数据科学与大数据技术', 'code': 'DS001', 'department': '计算机学院'},
            {'name': '人工智能', 'code': 'AI001', 'department': '计算机学院'},
            {'name': '网络工程', 'code': 'NE001', 'department': '计算机学院'},
            {'name': '信息安全', 'code': 'IS001', 'department': '计算机学院'},
            {'name': '电子信息工程', 'code': 'EE001', 'department': '电子工程学院'},
            {'name': '通信工程', 'code': 'CE001', 'department': '电子工程学院'},
            {'name': '自动化', 'code': 'AU001', 'department': '电子工程学院'},
            {'name': '电气工程及其自动化', 'code': 'EA001', 'department': '电子工程学院'},
            {'name': '机械工程', 'code': 'ME001', 'department': '机械工程学院'},
            {'name': '机械设计制造及其自动化', 'code': 'MD001', 'department': '机械工程学院'},
            {'name': '材料科学与工程', 'code': 'MS001', 'department': '材料学院'},
            {'name': '化学工程与工艺', 'code': 'CE002', 'department': '化学学院'},
            {'name': '生物工程', 'code': 'BE001', 'department': '生物学院'},
            {'name': '土木工程', 'code': 'CE003', 'department': '土木工程学院'},
            {'name': '建筑学', 'code': 'AR001', 'department': '建筑学院'},
            {'name': '工商管理', 'code': 'BM001', 'department': '管理学院'},
            {'name': '市场营销', 'code': 'MK001', 'department': '管理学院'},
            {'name': '会计学', 'code': 'AC001', 'department': '管理学院'},
            {'name': '金融学', 'code': 'FN001', 'department': '经济学院'},
            {'name': '国际经济与贸易', 'code': 'IT001', 'department': '经济学院'},
            {'name': '英语', 'code': 'EN001', 'department': '外国语学院'},
            {'name': '日语', 'code': 'JP001', 'department': '外国语学院'},
            {'name': '汉语言文学', 'code': 'CL001', 'department': '文学院'},
            {'name': '新闻学', 'code': 'JO001', 'department': '新闻学院'},
            {'name': '法学', 'code': 'LW001', 'department': '法学院'},
            {'name': '心理学', 'code': 'PS001', 'department': '心理学院'},
            {'name': '教育学', 'code': 'ED001', 'department': '教育学院'},
            {'name': '数学与应用数学', 'code': 'MA001', 'department': '数学学院'},
            {'name': '物理学', 'code': 'PH001', 'department': '物理学院'},
            {'name': '化学', 'code': 'CH001', 'department': '化学学院'},
            {'name': '生物科学', 'code': 'BS001', 'department': '生物学院'},
            {'name': '环境工程', 'code': 'EN002', 'department': '环境学院'},
            {'name': '食品科学与工程', 'code': 'FS001', 'department': '食品学院'},
            {'name': '艺术设计', 'code': 'AD001', 'department': '艺术学院'},
            {'name': '音乐学', 'code': 'MU001', 'department': '艺术学院'},
            {'name': '体育教育', 'code': 'PE001', 'department': '体育学院'},
            {'name': '护理学', 'code': 'NU001', 'department': '医学院'},
            {'name': '临床医学', 'code': 'CM001', 'department': '医学院'},
            {'name': '药学', 'code': 'PH002', 'department': '药学院'},
        ]
        
        for major_data in majors_data:
            major = Major(**major_data)
            db.session.add(major)
        db.session.commit()
    
    majors = Major.query.all()
    return render_template('auth/register.html', majors=majors)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')
            # 调试信息
            print(f"登录尝试失败 - 用户名: {username}")
            if user:
                print(f"用户存在但密码错误")
            else:
                print(f"用户不存在")
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == UserRole.ADMIN.value:
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == UserRole.DORM_MANAGER.value:
        return redirect(url_for('manager_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    student = current_user.student
    
    # 检查学生记录是否存在
    if not student:
        flash('学生信息不存在，请联系管理员', 'error')
        return redirect(url_for('index'))
    
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

@app.route('/dorms/browse')
def browse_dorms():
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

@app.route('/dorm/<int:dorm_id>')
def dorm_detail(dorm_id):
    dorm = Dormitory.query.get_or_404(dorm_id)
    
    # 获取评价统计
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

@app.route('/dorm/change', methods=['GET', 'POST'])
@login_required
def change_dorm():
    student = current_user.student
    
    # 检查学生记录是否存在
    if not student:
        flash('学生信息不存在，请联系管理员', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        target_dorm_id = request.form.get('target_dorm_id', type=int)
        reason = request.form.get('reason', '')
        
        if not target_dorm_id:
            flash('请选择目标宿舍', 'error')
            return redirect(url_for('change_dorm'))
        
        # 检查学生是否已有床位
        if not student.current_bed_id:
            flash('您当前没有床位，无法申请换宿', 'error')
            return redirect(url_for('change_dorm'))
        
        # 查询目标宿舍
        target_dorm = Dormitory.query.get_or_404(target_dorm_id)
        available_beds = [bed for bed in target_dorm.beds if bed.status == BedStatus.AVAILABLE.value]

        if not available_beds:
            flash('目标宿舍暂无空床', 'error')
            return redirect(url_for('change_dorm'))
        
        # 检查是否已有待审核的换宿申请
        pending_change = DormApplication.query.filter_by(
            student_id=student.id,
            application_type='change',
            status=ApplicationStatus.PENDING.value
        ).first()
        
        if pending_change:
            flash('您已有待审核的换宿申请，请等待审核结果', 'error')
            return redirect(url_for('student_dashboard'))
        
        # 创建换宿申请（不直接执行换宿）
        application = DormApplication(
            student_id=student.id,
            bed_id=available_beds[0].id,  # 目标床位
            target_dorm_id=target_dorm_id,
            application_type='change',
            status=ApplicationStatus.PENDING.value,
            reason=reason
        )
        
        # 将目标床位状态设为预留（等待审核）
        available_beds[0].status = BedStatus.RESERVED.value
        
        try:
            db.session.add(application)
            db.session.commit()
            flash('换宿申请已提交，请等待管理员审核', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'提交申请时发生错误：{str(e)}', 'error')

        return redirect(url_for('student_dashboard'))
    
    # 获取所有可用宿舍
    available_dorms = []
    for dorm in Dormitory.query.join(Building).filter(Building.gender == student.gender).all():
        if dorm.available_beds:
            available_dorms.append(dorm)
    
    return render_template('dorms/change.html', dorms=available_dorms)

@app.route('/team/create', methods=['GET', 'POST'])
@login_required
def create_team():
    student = current_user.student
    
    # 检查学生记录是否存在
    if not student:
        flash('学生信息不存在，请联系管理员', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        max_size = request.form.get('max_size', 4, type=int)
        
        # 生成邀请码
        import random
        import string
        invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        team = DormTeam(
            name=name,
            leader_id=student.id,
            max_size=max_size,
            invite_code=invite_code
        )
        db.session.add(team)
        
        # 将创建者加入团队
        student.team_id = team.id
        db.session.commit()
        
        flash(f'团队创建成功！邀请码：{invite_code}', 'success')
        return redirect(url_for('team_detail', team_id=team.id))
    
    return render_template('team/create.html')

@app.route('/team/<int:team_id>')
@login_required
def team_detail(team_id):
    student = current_user.student
    
    # 检查学生记录是否存在
    if not student:
        flash('学生信息不存在，请联系管理员', 'error')
        return redirect(url_for('index'))
    
    team = DormTeam.query.get_or_404(team_id)
    # 检查访问权限：只有团队成员可以查看
    if student.team_id != team.id:
        flash('您没有权限查看该团队信息', 'error')
        return redirect(url_for('student_dashboard'))
    return render_template('team/detail.html', team=team)

@app.route('/team/join', methods=['GET', 'POST'])
@login_required
def join_team_page():
    if request.method == 'POST':
        invite_code = request.form['invite_code']
        
        team = DormTeam.query.filter_by(invite_code=invite_code).first()
        if not team:
            flash('邀请码无效', 'error')
            return redirect(url_for('join_team_page'))
        
        if len(team.members) >= team.max_size:
            flash('团队已满', 'error')
            return redirect(url_for('join_team_page'))
        
        if current_user.student.team_id:
            flash('您已经加入了其他团队', 'error')
            return redirect(url_for('student_dashboard'))
        
        current_user.student.team_id = team.id
        db.session.commit()
        flash('成功加入团队', 'success')
        return redirect(url_for('team_detail', team_id=team.id))
    
    return render_template('team/join.html')

@app.route('/team/<int:team_id>/remove/<int:member_id>', methods=['POST'])
@login_required
def remove_team_member(team_id, member_id):
    team = DormTeam.query.get_or_404(team_id)
    if current_user.student.id != team.leader_id:
        flash('只有团队队长可以移除成员', 'error')
        return redirect(url_for('team_detail', team_id=team_id))
    
    member = Student.query.get_or_404(member_id)
    if member.team_id == team.id:
        member.team_id = None
        db.session.commit()
        flash('成员已被移除', 'success')
    return redirect(url_for('team_detail', team_id=team_id))

@app.route('/team/<int:team_id>/leave', methods=['POST'])
@login_required
def leave_team(team_id):
    team = DormTeam.query.get_or_404(team_id)
    if current_user.student.team_id != team.id:
        flash('您不是该团队成员', 'error')
        return redirect(url_for('student_dashboard'))
    
    if current_user.student.id == team.leader_id:
        flash('队长不能直接退出团队，请先转让队长身份或解散团队', 'error')
        return redirect(url_for('team_detail', team_id=team_id))
    
    current_user.student.team_id = None
    db.session.commit()
    flash('您已退出团队', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/team/<int:team_id>/delete', methods=['POST'])
@login_required
def delete_team(team_id):
    team = DormTeam.query.get_or_404(team_id)
    if current_user.student.id != team.leader_id:
        flash('只有团队队长可以解散团队', 'error')
        return redirect(url_for('team_detail', team_id=team_id))
    
    # 解除所有成员的团队关联
    for member in team.members:
        member.team_id = None
    
    db.session.delete(team)
    db.session.commit()
    flash('团队已解散', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/team/join', methods=['POST'])
@login_required
def join_team():
    invite_code = request.form['invite_code']
    
    team = DormTeam.query.filter_by(invite_code=invite_code).first()
    if not team:
        flash('邀请码无效', 'error')
        return redirect(url_for('student_dashboard'))
    
    if len(team.members) >= team.max_size:
        flash('团队已满', 'error')
        return redirect(url_for('student_dashboard'))
    
    current_user.student.team_id = team.id
    db.session.commit()
    flash('成功加入团队', 'success')
    return redirect(url_for('team_detail', team_id=team.id))

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    student = current_user.student
    
    if request.method == 'POST':
        # 更新基本信息
        student.name = request.form['name']
        student.phone = request.form.get('phone')
        student.email = request.form.get('email')
        
        # 更新生活习惯
        student.sleep_time = request.form.get('sleep_time')
        student.wake_time = request.form.get('wake_time')
        student.quietness = request.form.get('quietness', type=int)
        student.cleanliness = request.form.get('cleanliness', type=int)
        student.hobbies = request.form.get('hobbies')
        
        db.session.commit()
        flash('个人信息更新成功', 'success')
        return redirect(url_for('student_dashboard'))
    
    # 获取所有专业用于选择
    majors = Major.query.all()
    return render_template('profile.html', student=student, majors=majors)

@app.route('/roommate/match')
@login_required
def roommate_match():
    student = current_user.student
    
    # 检查学生记录是否存在
    if not student:
        flash('学生信息不存在，请联系管理员', 'error')
        return redirect(url_for('index'))
    
    # 基于生活习惯匹配室友
    query = Student.query.filter(
        Student.id != student.id,
        Student.gender == student.gender,
        Student.current_bed_id == None,  # 未分配宿舍
        Student.team_id == None  # 未加入团队
    )
    
    # 计算匹配度
    matches = []
    for s in query.all():
        score = 0
        # 作息时间匹配
        if s.sleep_time == student.sleep_time:
            score += 30
        if s.wake_time == student.wake_time:
            score += 30
        # 生活习惯匹配
        if s.quietness and student.quietness:
            score += max(0, 20 - abs(s.quietness - student.quietness) * 5)
        if s.cleanliness and student.cleanliness:
            score += max(0, 20 - abs(s.cleanliness - student.cleanliness) * 5)
        
        matches.append({
            'student': s,
            'score': score
        })
    
    # 按匹配度排序
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    return render_template('roommate/match.html', matches=matches[:10])

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != UserRole.ADMIN.value:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
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
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_applications=recent_applications)

@app.route('/admin/application/<int:app_id>/process', methods=['POST'])
@login_required
def process_application(app_id):
    if current_user.role not in [UserRole.ADMIN.value, UserRole.DORM_MANAGER.value]:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    application = DormApplication.query.get_or_404(app_id)
    action = request.form['action']
    remarks = request.form.get('remarks', '')
    
    if action == 'approve':
        application.status = ApplicationStatus.APPROVED.value
        # 分配床位
        bed = application.bed
        bed.status = BedStatus.OCCUPIED.value
        application.student.current_bed_id = bed.id
        flash('申请已批准', 'success')
        
    elif action == 'reject':
        application.status = ApplicationStatus.REJECTED.value
        # 释放预留的床位
        if application.bed.status == BedStatus.RESERVED.value:
            application.bed.status = BedStatus.AVAILABLE.value
        flash('申请已拒绝', 'info')
    
    application.processed_at = datetime.utcnow()
    application.processed_by = current_user.id
    application.remarks = remarks
    
    db.session.commit()
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/students')
@login_required
def admin_students():
    if current_user.role != UserRole.ADMIN.value:#如果用户不是管理员，则返回主页
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    # 获取筛选参数
    search = request.args.get('search', '')
    major_id = request.args.get('major_id', type=int)
    grade = request.args.get('grade', type=int)
    
    # 构建查询
    query = Student.query.join(User).join(Major, Student.major_id == Major.id)
    
    if search:
        query = query.filter(
            db.or_(
                Student.name.contains(search),
                Student.student_id.contains(search),
                Student.phone.contains(search)
            )
        )
    if major_id:
        query = query.filter(Student.major_id == major_id)
    if grade:
        query = query.filter(Student.grade == grade)
    
    # 分页
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=20)
    
    # 获取专业列表用于筛选
    majors = Major.query.all()
    
    return render_template('admin/students.html',
                         students=pagination.items,
                         pagination=pagination,
                         majors=majors,
                         search=search,
                         major_id=major_id,
                         grade=grade)

@app.route('/admin/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.role != UserRole.ADMIN.value:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        # 更新学生信息
        student.name = request.form['name']
        student.phone = request.form.get('phone')
        student.email = request.form.get('email')
        student.major_id = request.form.get('major_id', type=int)
        student.grade = request.form.get('grade', type=int)
        
        # 更新生活习惯
        student.sleep_time = request.form.get('sleep_time')
        student.wake_time = request.form.get('wake_time')
        student.quietness = request.form.get('quietness', type=int)
        student.cleanliness = request.form.get('cleanliness', type=int)
        student.hobbies = request.form.get('hobbies')
        
        db.session.commit()
        flash('学生信息更新成功', 'success')
        return redirect(url_for('admin_students'))
    
    majors = Major.query.all()
    return render_template('admin/edit_student.html', student=student, majors=majors)

@app.route('/admin/students/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != UserRole.ADMIN.value:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    
    # 检查是否有住宿记录
    if student.current_bed_id:
        flash('该学生有住宿记录，无法删除', 'error')
        return redirect(url_for('admin_students'))
    
    # 删除学生记录
    db.session.delete(student)
    db.session.commit()
    flash('学生信息已删除', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/buildings')
@login_required
def admin_buildings():
    if current_user.role != UserRole.ADMIN.value:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    buildings = Building.query.all()
    return render_template('admin/buildings.html', buildings=buildings)

@app.route('/admin/buildings/create', methods=['GET', 'POST'])
@login_required
def create_building():
    if current_user.role != UserRole.ADMIN.value:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        gender = request.form['gender']
        total_floors = request.form.get('total_floors', type=int)
        location = request.form.get('location')
        facilities = request.form.get('facilities')
        description = request.form.get('description')
        
        building = Building(
            name=name,
            gender=gender,
            total_floors=total_floors,
            location=location,
            facilities=facilities,
            description=description
        )
        db.session.add(building)
        db.session.commit()
        
        flash('楼栋创建成功', 'success')
        return redirect(url_for('admin_buildings'))
    
    return render_template('admin/create_building.html')

@app.route('/admin/buildings/<int:building_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_building(building_id):
    if current_user.role != UserRole.ADMIN.value:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    building = Building.query.get_or_404(building_id)
    
    if request.method == 'POST':
        building.name = request.form['name']
        building.gender = request.form['gender']
        building.total_floors = request.form.get('total_floors', type=int)
        building.location = request.form.get('location')
        building.facilities = request.form.get('facilities')
        building.description = request.form.get('description')
        
        db.session.commit()
        flash('楼栋信息更新成功', 'success')
        return redirect(url_for('admin_buildings'))
    
    return render_template('admin/edit_building.html', building=building)

@app.route('/admin/buildings/<int:building_id>/delete', methods=['POST'])
@login_required
def delete_building(building_id):
    if current_user.role != UserRole.ADMIN.value:
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    building = Building.query.get_or_404(building_id)
    
    # 检查是否有宿舍记录
    if building.dormitories:
        flash('该楼栋有宿舍记录，无法删除', 'error')
        return redirect(url_for('admin_buildings'))
    
    db.session.delete(building)
    db.session.commit()
    flash('楼栋已删除', 'success')
    return redirect(url_for('admin_buildings'))

@app.route('/messages')
@login_required
def messages():
    student = current_user.student
    
    # 获取收到的消息
    received_messages = Message.query.filter_by(receiver_id=student.id).order_by(Message.created_at.desc()).all()
    
    # 获取发送的消息
    sent_messages = Message.query.filter_by(sender_id=student.id).order_by(Message.created_at.desc()).all()
    
    # 获取未读消息数量
    unread_count = Message.query.filter_by(receiver_id=student.id, is_read=False).count()
    
    return render_template('messages/list.html',
                         received_messages=received_messages,
                         sent_messages=sent_messages,
                         unread_count=unread_count)

@app.route('/messages/send', methods=['GET', 'POST'])
@login_required
def send_message():
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id', type=int)
        content = request.form.get('content')
        
        if not receiver_id or not content:
            flash('请填写完整信息', 'error')
            return redirect(url_for('send_message'))
        
        # 检查接收者是否存在
        receiver = Student.query.get(receiver_id)
        if not receiver:
            flash('接收者不存在', 'error')
            return redirect(url_for('send_message'))
        
        # 创建消息
        message = Message(
            sender_id=current_user.student.id,
            receiver_id=receiver_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        
        flash('消息发送成功', 'success')
        return redirect(url_for('messages'))
    
    # 获取所有学生用于选择接收者
    students = Student.query.filter(Student.id != current_user.student.id).all()
    return render_template('messages/send.html', students=students)

@app.route('/messages/<int:message_id>/read', methods=['POST'])
@login_required
def mark_message_read(message_id):
    message = Message.query.get_or_404(message_id)
    
    # 检查权限：只有接收者可以标记为已读
    if message.receiver_id != current_user.student.id:
        flash('权限不足', 'error')
        return redirect(url_for('messages'))
    
    message.is_read = True
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    # 检查权限：发送者或接收者可以删除
    if message.sender_id != current_user.student.id and message.receiver_id != current_user.student.id:
        flash('权限不足', 'error')
        return redirect(url_for('messages'))
    
    db.session.delete(message)
    db.session.commit()
    flash('消息已删除', 'success')
    return redirect(url_for('messages'))

@app.route('/dorm/<int:dorm_id>/review', methods=['GET', 'POST'])
@login_required
def review_dorm(dorm_id):
    dorm = Dormitory.query.get_or_404(dorm_id)
    
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        environment_rating = request.form.get('environment_rating', type=int)
        facilities_rating = request.form.get('facilities_rating', type=int)
        location_rating = request.form.get('location_rating', type=int)
        comment = request.form.get('comment')
        
        # 检查是否已经评价过
        existing_review = DormReview.query.filter_by(
            dorm_id=dorm_id,
            student_id=current_user.student.id
        ).first()
        
        if existing_review:
            # 更新现有评价
            existing_review.rating = rating
            existing_review.environment_rating = environment_rating
            existing_review.facilities_rating = facilities_rating
            existing_review.location_rating = location_rating
            existing_review.comment = comment
            flash('评价已更新', 'success')
        else:
            # 创建新评价
            review = DormReview(
                dorm_id=dorm_id,
                student_id=current_user.student.id,
                rating=rating,
                environment_rating=environment_rating,
                facilities_rating=facilities_rating,
                location_rating=location_rating,
                comment=comment
            )
            db.session.add(review)
            flash('评价提交成功', 'success')
        
        db.session.commit()
        return redirect(url_for('dorm_detail', dorm_id=dorm_id))
    
    # 检查是否已经评价过
    existing_review = DormReview.query.filter_by(
        dorm_id=dorm_id,
        student_id=current_user.student.id
    ).first()
    
    return render_template('dorms/review.html', dorm=dorm, existing_review=existing_review)

@app.route('/reviews/my')
@login_required
def my_reviews():
    student = current_user.student
    reviews = DormReview.query.filter_by(student_id=student.id).order_by(DormReview.created_at.desc()).all()
    
    return render_template('reviews/my.html', reviews=reviews)

@app.route('/attendance/check_in', methods=['POST'])
@login_required
def check_in():
    today = date.today()
    # 检查是否已经打卡
    record = AttendanceRecord.query.filter_by(user_id=current_user.id, date=today).first()
    if record:
        return jsonify({"message": "今天已经打过卡了！"}), 400

    # 创建新的打卡记录
    new_record = AttendanceRecord(user_id=current_user.id, date=today, status='checked_in')
    db.session.add(new_record)
    db.session.commit()
    return jsonify({"message": "打卡成功！"}), 200

@app.route('/attendance/statistics', methods=['GET'])
@login_required
def attendance_statistics():
    if current_user.role != UserRole.ADMIN.value:
        return jsonify({"message": "无权限访问！"}), 403

    today = date.today()
    total_users = User.query.filter_by(role=UserRole.STUDENT.value).count()
    checked_in_count = AttendanceRecord.query.filter_by(date=today, status='checked_in').count()
    not_checked_in_count = total_users - checked_in_count

    return jsonify({
        "date": today.strftime('%Y-%m-%d'),
        "checked_in": checked_in_count,
        "not_checked_in": not_checked_in_count
    })

# API 路由
@app.route('/api/dorms/available')
def api_available_dorms():
    """返回可用宿舍的JSON数据"""
    gender = request.args.get('gender')
    capacity = request.args.get('capacity', type=int)
    
    query = Dormitory.query.join(Building)
    
    if gender:
        query = query.filter(Building.gender == gender)
    if capacity:
        query = query.filter(Dormitory.capacity == capacity)
    
    dorms = query.all()
    
    result = []
    for dorm in dorms:
        result.append({
            'id': dorm.id,
            'building': dorm.building.name,
            'room_number': dorm.room_number,
            'floor': dorm.floor,
            'capacity': dorm.capacity,
            'available_beds': len(dorm.available_beds),
            'monthly_rent': dorm.monthly_rent,
            'facilities': {
                'ac': dorm.has_ac,
                'bathroom': dorm.has_bathroom,
                'balcony': dorm.has_balcony,
                'water_heater': dorm.has_water_heater
            }
        })
    
    return jsonify(result)

@app.route('/api/bed/<int:bed_id>/status')
def api_bed_status(bed_id):
    """获取床位状态"""
    bed = Bed.query.get_or_404(bed_id)
    return jsonify({
        'id': bed.id,
        'status': bed.status,
        'bed_number': bed.bed_number,
        'position': bed.position,
        'dorm_id': bed.dorm_id,
        'occupant': {
            'name': bed.current_student.name,
            'student_id': bed.current_student.student_id,
            'major': bed.current_student.major.name
        } if bed.current_student else None
    })

@app.route('/api/statistics/occupancy')
def api_occupancy_stats():
    """获取入住率统计"""
    buildings = Building.query.all()
    stats = []
    
    for building in buildings:
        total_beds = 0
        occupied_beds = 0
        
        for dorm in building.dormitories:
            total_beds += dorm.capacity
            occupied_beds += dorm.occupied_count
        
        stats.append({
            'building': building.name,
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'occupancy_rate': (occupied_beds / total_beds * 100) if total_beds > 0 else 0
        })
    
    return jsonify(stats)

# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# 上下文处理器
@app.context_processor
def inject_enums():
    return dict(
        UserRole=UserRole,
        BedStatus=BedStatus,
        ApplicationStatus=ApplicationStatus
    )

# 模板辅助函数：生成分页URL
@app.template_global()
def url_for_page(endpoint, page_num, **kwargs):
    """生成分页URL，排除page参数避免重复"""
    # 从request.args中获取所有筛选参数，但排除page
    args = {}
    for key, value in request.args.items():
        if key != 'page' and value:
            args[key] = value
    # 合并传入的kwargs
    args.update(kwargs)
    # 添加新的page参数
    args['page'] = page_num
    return url_for(endpoint, **args)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # 使用5001端口，避免与macOS的AirPlay Receiver冲突
    app.run(debug=True, port=5001)
