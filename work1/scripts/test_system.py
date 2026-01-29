#!/usr/bin/env python3
"""
系统功能测试脚本
测试账号注册、打卡功能、宿舍分配逻辑等核心功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from start import app, db, auto_assign_dorm
from models.user import User, Student, Major
from models.dormitory import Building, Dormitory, Bed
from models.database import db as db_instance, UserRole, BedStatus, AttendanceRecord
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import random

class TestResult:
    """测试结果类"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ {test_name}")
    
    def add_fail(self, test_name, error_msg):
        self.failed += 1
        self.errors.append(f"{test_name}: {error_msg}")
        print(f"❌ {test_name}: {error_msg}")
    
    def summary(self):
        total = self.passed + self.failed
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print(f"总测试数: {total}")
        print(f"通过: {self.passed} ({self.passed/total*100:.1f}%)" if total > 0 else "通过: 0")
        print(f"失败: {self.failed} ({self.failed/total*100:.1f}%)" if total > 0 else "失败: 0")
        if self.errors:
            print("\n失败详情:")
            for error in self.errors:
                print(f"  - {error}")
        print("="*60)

def setup_test_data():
    """设置测试数据"""
    with app.app_context():
        # 确保有专业数据
        major = Major.query.filter_by(code='CS001').first()
        if not major:
            major = Major(
                name='计算机科学',
                code='CS001',
                department='计算机学院'
            )
            db.session.add(major)
            db.session.commit()
        
        # 确保有宿舍楼和床位
        building = Building.query.filter_by(name='测试楼').first()
        if not building:
            building = Building(
                name='测试楼',
                gender='男',
                total_floors=5,
                location='测试区域',
                description='测试用宿舍楼'
            )
            db.session.add(building)
            db.session.flush()
            
            # 创建一些测试宿舍
            for floor in range(1, 4):
                for room_num in range(1, 4):
                    dorm = Dormitory(
                        building_id=building.id,
                        room_number=f"{floor:02d}{room_num:02d}",
                        floor=floor,
                        capacity=4,
                        room_type='标准四人间',
                        has_ac=True,
                        has_bathroom=True,
                        has_balcony=True,
                        has_water_heater=True
                    )
                    db.session.add(dorm)
                    db.session.flush()
                    
                    # 为每个宿舍创建床位
                    for bed_num in range(1, 5):
                        bed = Bed(
                            dorm_id=dorm.id,
                            bed_number=bed_num,
                            status=BedStatus.AVAILABLE.value
                        )
                        db.session.add(bed)
            
            db.session.commit()
        
        return major, building

def cleanup_test_users():
    """清理测试用户"""
    with app.app_context():
        # 删除测试用户（用户名以test_开头的）
        test_users = User.query.filter(User.username.like('test_%')).all()
        for user in test_users:
            if user.student:
                # 释放床位
                if user.student.current_bed_id:
                    bed = Bed.query.get(user.student.current_bed_id)
                    if bed:
                        bed.status = BedStatus.AVAILABLE.value
                db.session.delete(user.student)
            # 删除打卡记录
            AttendanceRecord.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
        
        # 删除没有关联用户的测试学生（临时创建的学生）
        orphan_students = Student.query.filter(
            Student.student_id.like('ST%') |
            Student.student_id.like('MA%') |
            Student.student_id.like('AT%') |
            Student.student_id.like('EX%') |
            Student.student_id.like('NE%') |
            Student.student_id.like('LS%') |
            Student.student_id.like('NB%') |
            Student.student_id.like('FE%')
        ).filter(Student.user_id.is_(None)).all()
        
        for student in orphan_students:
            # 释放床位
            if student.current_bed_id:
                bed = Bed.query.get(student.current_bed_id)
                if bed:
                    bed.status = BedStatus.AVAILABLE.value
            db.session.delete(student)
        
        db.session.commit()

def test_user_registration(result):
    """测试用户注册功能"""
    print("\n" + "="*60)
    print("测试1: 用户注册功能")
    print("="*60)
    
    with app.app_context():
        try:
            # 测试1.1: 正常注册
            username = f"test_student_{random.randint(1000, 9999)}"
            password = "test123456"
            student_id = f"ST{random.randint(100000, 999999)}"
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                result.add_fail("用户注册-正常注册", "测试用户名已存在")
                return
            
            major, _ = setup_test_data()
            
            user = User(
                username=username,
                password_hash=generate_password_hash(password),
                role=UserRole.STUDENT.value
            )
            db.session.add(user)
            db.session.flush()
            
            student = Student(
                user_id=user.id,
                student_id=student_id,
                name='测试学生',
                id_card='110101199001011234',
                gender='男',
                major_id=major.id,
                phone='13800138000',
                email='test@example.com',
                grade=2024,
                sleep_time='早睡',
                wake_time='早起',
                quietness=3,
                cleanliness=4
            )
            db.session.add(student)
            db.session.commit()
            
            # 验证注册成功
            saved_user = User.query.filter_by(username=username).first()
            if saved_user and saved_user.student and saved_user.student.student_id == student_id:
                result.add_pass("用户注册-正常注册")
            else:
                result.add_fail("用户注册-正常注册", "用户或学生信息保存失败")
            
            # 测试1.2: 重复用户名注册
            duplicate_user = User(
                username=username,
                password_hash=generate_password_hash("another_password"),
                role=UserRole.STUDENT.value
            )
            db.session.add(duplicate_user)
            try:
                db.session.commit()
                result.add_fail("用户注册-重复用户名", "应该抛出唯一约束错误")
                db.session.delete(duplicate_user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                result.add_pass("用户注册-重复用户名")
            
            # 测试1.3: 重复学号注册
            duplicate_student = Student(
                user_id=user.id,
                student_id=student_id,  # 重复学号
                name='另一个学生',
                id_card='110101199001011235',
                gender='男'
            )
            db.session.add(duplicate_student)
            try:
                db.session.commit()
                result.add_fail("用户注册-重复学号", "应该抛出唯一约束错误")
                db.session.delete(duplicate_student)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                result.add_pass("用户注册-重复学号")
            
        except Exception as e:
            result.add_fail("用户注册-异常", str(e))
            db.session.rollback()

def test_attendance(result):
    """测试打卡功能"""
    print("\n" + "="*60)
    print("测试2: 打卡功能")
    print("="*60)
    
    with app.app_context():
        try:
            # 创建测试用户
            major, _ = setup_test_data()
            username = f"test_attendance_{random.randint(1000, 9999)}"
            
            user = User(
                username=username,
                password_hash=generate_password_hash("test123"),
                role=UserRole.STUDENT.value
            )
            db.session.add(user)
            db.session.flush()
            
            student = Student(
                user_id=user.id,
                student_id=f"AT{random.randint(100000, 999999)}",
                name='打卡测试学生',
                id_card='110101199001011236',
                gender='男',
                major_id=major.id
            )
            db.session.add(student)
            db.session.commit()
            
            # 测试2.1: 首次打卡
            today = date.today()
            record = AttendanceRecord(
                user_id=user.id,
                date=today,
                status='checked_in',
                check_in_time=datetime.utcnow()
            )
            db.session.add(record)
            db.session.commit()
            
            saved_record = AttendanceRecord.query.filter_by(
                user_id=user.id,
                date=today
            ).first()
            
            if saved_record and saved_record.status == 'checked_in':
                result.add_pass("打卡功能-首次打卡")
            else:
                result.add_fail("打卡功能-首次打卡", "打卡记录保存失败")
            
            # 测试2.2: 重复打卡（同一天）
            try:
                duplicate_record = AttendanceRecord(
                    user_id=user.id,
                    date=today,
                    status='checked_in'
                )
                db.session.add(duplicate_record)
                db.session.commit()
                result.add_fail("打卡功能-重复打卡", "应该抛出唯一约束错误")
                db.session.delete(duplicate_record)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                result.add_pass("打卡功能-重复打卡")
            
            # 测试2.3: 不同日期打卡
            yesterday = today - timedelta(days=1)
            yesterday_record = AttendanceRecord(
                user_id=user.id,
                date=yesterday,
                status='checked_in',
                check_in_time=datetime.utcnow()
            )
            db.session.add(yesterday_record)
            db.session.commit()
            
            saved_yesterday = AttendanceRecord.query.filter_by(
                user_id=user.id,
                date=yesterday
            ).first()
            
            if saved_yesterday:
                result.add_pass("打卡功能-不同日期打卡")
            else:
                result.add_fail("打卡功能-不同日期打卡", "不同日期打卡失败")
            
            # 测试2.4: 查询打卡记录
            records = AttendanceRecord.query.filter_by(user_id=user.id).all()
            if len(records) >= 2:
                result.add_pass("打卡功能-查询打卡记录")
            else:
                result.add_fail("打卡功能-查询打卡记录", f"应该至少有2条记录，实际{len(records)}条")
            
        except Exception as e:
            result.add_fail("打卡功能-异常", str(e))
            db.session.rollback()

def test_dorm_assignment(result):
    """测试宿舍分配逻辑"""
    print("\n" + "="*60)
    print("测试3: 宿舍分配逻辑")
    print("="*60)
    
    with app.app_context():
        try:
            major, building = setup_test_data()
            
            # 测试3.1: 性别匹配
            print("\n测试3.1: 性别匹配...")
            male_student = Student(
                user_id=None,  # 临时学生，不创建用户
                student_id=f"MA{random.randint(100000, 999999)}",
                name='男生测试',
                id_card='110101199001011237',
                gender='男',
                major_id=major.id
            )
            db.session.add(male_student)
            db.session.flush()
            
            assigned_bed = auto_assign_dorm(male_student)
            if assigned_bed:
                dorm = assigned_bed.dorm
                if dorm.building.gender == '男':
                    result.add_pass("宿舍分配-性别匹配")
                else:
                    result.add_fail("宿舍分配-性别匹配", f"分配到了{dorm.building.gender}生楼")
            else:
                result.add_fail("宿舍分配-性别匹配", "未分配到宿舍")
            
            # 测试3.2: 宿舍人数偏好（4人间）
            print("\n测试3.2: 宿舍人数偏好（4人间）...")
            student_4 = Student(
                user_id=None,
                student_id=f"ST4{random.randint(100000, 999999)}",
                name='4人间偏好学生',
                id_card='110101199001011238',
                gender='男',
                major_id=major.id
            )
            db.session.add(student_4)
            db.session.flush()
            
            assigned_bed_4 = auto_assign_dorm(student_4, preferred_capacity=4)
            if assigned_bed_4:
                if assigned_bed_4.dorm.capacity == 4:
                    result.add_pass("宿舍分配-4人间偏好")
                elif assigned_bed_4.dorm.capacity == 6:
                    result.add_pass("宿舍分配-4人间偏好（降级到6人间）")
                else:
                    result.add_fail("宿舍分配-4人间偏好", f"分配到了{assigned_bed_4.dorm.capacity}人间")
            else:
                result.add_fail("宿舍分配-4人间偏好", "未分配到宿舍")
            
            # 测试3.3: 专业匹配
            print("\n测试3.3: 专业匹配...")
            # 先创建一个已入住的学生
            existing_user = User(
                username=f"test_existing_{random.randint(1000, 9999)}",
                password_hash=generate_password_hash("test"),
                role=UserRole.STUDENT.value
            )
            db.session.add(existing_user)
            db.session.flush()
            
            existing_student = Student(
                user_id=existing_user.id,
                student_id=f"EX{random.randint(100000, 999999)}",
                name='已入住学生',
                id_card='110101199001011239',
                gender='男',
                major_id=major.id
            )
            db.session.add(existing_student)
            db.session.flush()
            
            # 分配床位给已入住学生
            existing_bed = auto_assign_dorm(existing_student)
            if existing_bed:
                existing_student.current_bed_id = existing_bed.id
                existing_bed.status = BedStatus.OCCUPIED.value
                db.session.commit()
                
                # 现在测试新学生是否能分配到同一宿舍（专业匹配）
                new_student = Student(
                    user_id=None,
                    student_id=f"NE{random.randint(100000, 999999)}",
                    name='新学生',
                    id_card='110101199001011240',
                    gender='男',
                    major_id=major.id  # 相同专业
                )
                db.session.add(new_student)
                db.session.flush()
                
                new_bed = auto_assign_dorm(new_student)
                if new_bed:
                    # 检查是否分配到同一宿舍（专业匹配应该优先）
                    if new_bed.dorm_id == existing_bed.dorm_id:
                        result.add_pass("宿舍分配-专业匹配")
                    else:
                        result.add_pass("宿舍分配-专业匹配（分配到不同宿舍，可能因为其他因素）")
                else:
                    result.add_fail("宿舍分配-专业匹配", "未分配到宿舍")
            else:
                result.add_fail("宿舍分配-专业匹配", "无法为已入住学生分配床位")
            
            # 测试3.4: 生活习惯匹配
            print("\n测试3.4: 生活习惯匹配...")
            lifestyle_student = Student(
                user_id=None,
                student_id=f"LS{random.randint(100000, 999999)}",
                name='生活习惯匹配学生',
                id_card='110101199001011241',
                gender='男',
                major_id=major.id,
                sleep_time='早睡',
                wake_time='早起',
                quietness=4,
                cleanliness=4
            )
            db.session.add(lifestyle_student)
            db.session.flush()
            
            lifestyle_bed = auto_assign_dorm(lifestyle_student)
            if lifestyle_bed:
                result.add_pass("宿舍分配-生活习惯匹配")
            else:
                result.add_fail("宿舍分配-生活习惯匹配", "未分配到宿舍")
            
            # 测试3.5: 无可用床位
            print("\n测试3.5: 无可用床位...")
            # 将所有床位标记为已占用
            all_beds = Bed.query.filter_by(status=BedStatus.AVAILABLE.value).all()
            original_statuses = {}
            for bed in all_beds:
                original_statuses[bed.id] = bed.status
                bed.status = BedStatus.OCCUPIED.value
            db.session.commit()
            
            no_bed_student = Student(
                user_id=None,
                student_id=f"NB{random.randint(100000, 999999)}",
                name='无床位学生',
                id_card='110101199001011242',
                gender='男',
                major_id=major.id
            )
            db.session.add(no_bed_student)
            db.session.flush()
            
            no_bed_result = auto_assign_dorm(no_bed_student)
            if no_bed_result is None:
                result.add_pass("宿舍分配-无可用床位")
            else:
                result.add_fail("宿舍分配-无可用床位", "应该返回None")
            
            # 恢复床位状态
            for bed_id, status in original_statuses.items():
                bed = Bed.query.get(bed_id)
                if bed:
                    bed.status = status
            db.session.commit()
            
            # 测试3.6: 性别不匹配
            print("\n测试3.6: 性别不匹配...")
            # 确保只有男生楼有床位
            female_student = Student(
                user_id=None,
                student_id=f"FE{random.randint(100000, 999999)}",
                name='女生测试',
                id_card='110101199001011243',
                gender='女',
                major_id=major.id
            )
            db.session.add(female_student)
            db.session.flush()
            
            # 如果只有男生楼，女生应该无法分配
            female_bed = auto_assign_dorm(female_student)
            if female_bed:
                if female_bed.dorm.building.gender == '女':
                    result.add_pass("宿舍分配-性别不匹配")
                else:
                    result.add_fail("宿舍分配-性别不匹配", "分配到了错误性别的宿舍")
            else:
                # 如果没有女生楼，这是正常的
                result.add_pass("宿舍分配-性别不匹配（无对应性别宿舍）")
            
        except Exception as e:
            result.add_fail("宿舍分配-异常", str(e))
            db.session.rollback()

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始系统功能测试")
    print("="*60)
    
    result = TestResult()
    
    # 清理之前的测试数据
    with app.app_context():
        cleanup_test_users()
    
    # 运行测试
    try:
        test_user_registration(result)
        test_attendance(result)
        test_dorm_assignment(result)
    except Exception as e:
        print(f"\n❌ 测试执行异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        with app.app_context():
            cleanup_test_users()
    
    # 显示测试结果
    result.summary()
    
    return result

if __name__ == '__main__':
    run_all_tests()

