from models.database import db, UserRole
from models.user import User, Student
from werkzeug.security import generate_password_hash
from datetime import datetime

class UserService:
    def register_user(self, form_data):
        """用户注册服务"""
        # 验证用户名是否已存在
        if User.query.filter_by(username=form_data['username']).first():
            return {'success': False, 'message': '用户名已存在'}
            
        # 验证学号是否已存在
        if Student.query.filter_by(student_id=form_data['student_id']).first():
            return {'success': False, 'message': '学号已被注册'}
            
        try:
            # 创建用户账号
            user = User(
                username=form_data['username'],
                password_hash=generate_password_hash(form_data['password']),
                role=UserRole.STUDENT.value
            )
            db.session.add(user)
            db.session.flush()  # 获取用户ID
            
            # 创建学生信息
            student = Student(
                user_id=user.id,
                student_id=form_data['student_id'],
                name=form_data['name'],
                id_card=form_data['id_card'],
                gender=form_data['gender'],
                phone=form_data['phone'],
                email=form_data['email'],
                major_id=form_data['major_id'],
                grade=form_data['grade'],
                sleep_time=form_data.get('sleep_time'),
                wake_time=form_data.get('wake_time'),
                quietness=form_data.get('quietness'),
                cleanliness=form_data.get('cleanliness'),
                hobbies=form_data.get('hobbies')
            )
            db.session.add(student)
            db.session.commit()
            
            return {'success': True, 'message': '注册成功'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}