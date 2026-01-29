import unittest
from app import create_app, db
from models.user import User
from models.dormitory import Dormitory, Bed
from models.application import DormApplication
from models.database import UserRole, BedStatus, ApplicationStatus
from werkzeug.security import generate_password_hash

class TestDormSystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_user_registration(self):
        """测试用户注册"""
        response = self.client.post('/register', data={
            'username': 'testuser',
            'password': 'Test123456',
            'student_id': '2021001',
            'name': '测试用户',
            'id_card': '123456200001010001',
            'gender': 'male',
            'phone': '13800138000',
            'email': 'test@example.com',
            'major_id': 1,
            'grade': 2021
        })
        self.assertEqual(response.status_code, 302)
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        
    def test_dorm_application(self):
        """测试宿舍申请"""
        # 创建测试用户
        user = User(
            username='testuser',
            password_hash=generate_password_hash('Test123456'),
            role=UserRole.STUDENT.value
        )
        db.session.add(user)
        db.session.commit()
        
        # 登录
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'Test123456'
        })
        
        # 创建测试宿舍
        dorm = Dormitory(
            building_id=1,
            room_number='101',
            floor=1,
            capacity=4
        )
        db.session.add(dorm)
        db.session.commit()
        
        # 提交申请
        response = self.client.post('/dorm/apply', data={
            'dorm_id': dorm.id,
            'reason': 'test application'
        })
        self.assertEqual(response.status_code, 302)
        
        # 验证申请是否创建
        application = DormApplication.query.filter_by(
            student_id=user.student.id
        ).first()
        self.assertIsNotNone(application)
        self.assertEqual(application.status, ApplicationStatus.PENDING.value)
        
if __name__ == '__main__':
    unittest.main()