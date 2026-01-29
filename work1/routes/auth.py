from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from models.database import db
from models.user import User, Student, Major, UserRole

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
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
        
        # 检查用户名是否存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('auth.register'))
        
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
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    majors = Major.query.all()
    return render_template('auth/register.html', majors=majors)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
