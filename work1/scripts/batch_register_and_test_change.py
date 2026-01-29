#!/usr/bin/env python3
"""
批量注册用户填满宿舍，并测试宿舍更换功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from start import app, db, auto_assign_dorm
from models.user import User, Student, Major
from models.dormitory import Building, Dormitory, Bed
from models.database import UserRole, BedStatus
from werkzeug.security import generate_password_hash
from datetime import datetime
import random

def get_available_bed_count():
    """获取可用床位数量"""
    with app.app_context():
        return Bed.query.filter_by(status=BedStatus.AVAILABLE.value).count()

def batch_register_students():
    """批量注册学生，填满宿舍"""
    with app.app_context():
        print("="*60)
        print("开始批量注册学生")
        print("="*60)
        
        # 获取可用床位数量
        available_beds = get_available_bed_count()
        print(f"当前可用床位数量: {available_beds}")
        
        if available_beds == 0:
            print("⚠️  没有可用床位，无法注册新学生")
            return
        
        # 获取专业列表
        majors = Major.query.all()
        if not majors:
            print("⚠️  没有专业数据，请先创建专业")
            return
        
        # 生成姓名列表
        surnames = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴', 
                   '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗']
        given_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军',
                      '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞',
                      '平', '刚', '桂英', '建华', '文', '华', '红', '建国', '云', '鹏']
        
        registered_count = 0
        failed_count = 0
        
        # 批量注册，直到床位填满
        while available_beds > 0:
            try:
                # 生成随机信息
                username = f"student_{random.randint(100000, 999999)}"
                student_id = f"ST{random.randint(1000000, 9999999)}"
                name = random.choice(surnames) + random.choice(given_names)
                gender = random.choice(['男', '女'])
                major = random.choice(majors)
                
                # 检查用户名和学号是否已存在
                if User.query.filter_by(username=username).first():
                    continue
                if Student.query.filter_by(student_id=student_id).first():
                    continue
                
                # 创建用户
                user = User(
                    username=username,
                    password_hash=generate_password_hash("123456"),
                    role=UserRole.STUDENT.value
                )
                db.session.add(user)
                db.session.flush()
                
                # 创建学生
                student = Student(
                    user_id=user.id,
                    student_id=student_id,
                    name=name,
                    id_card=f"110101{random.randint(19900101, 20051231)}{random.randint(1000, 9999)}",
                    gender=gender,
                    major_id=major.id,
                    phone=f"1{random.randint(3, 9)}{random.randint(100000000, 999999999)}",
                    email=f"{username}@example.com",
                    grade=2024,
                    sleep_time=random.choice(['早睡', '正常', '晚睡']),
                    wake_time=random.choice(['早起', '正常', '晚起']),
                    quietness=random.randint(1, 5),
                    cleanliness=random.randint(1, 5),
                    hobbies=random.choice(['阅读', '运动', '音乐', '游戏', '旅行', '摄影'])
                )
                db.session.add(student)
                db.session.flush()
                
                # 自动分配宿舍
                assigned_bed = auto_assign_dorm(student, preferred_capacity=random.choice([4, 6, None]))
                if assigned_bed:
                    student.current_bed_id = assigned_bed.id
                    assigned_bed.status = BedStatus.OCCUPIED.value
                    registered_count += 1
                    
                    if registered_count % 50 == 0:
                        print(f"已注册 {registered_count} 名学生...")
                else:
                    # 如果没有分配到床位，删除刚创建的用户和学生
                    db.session.delete(student)
                    db.session.delete(user)
                    db.session.rollback()
                    print(f"⚠️  学生 {name} 无法分配到床位，跳过")
                    failed_count += 1
                    break  # 没有可用床位了，退出循环
                
                db.session.commit()
                
                # 更新可用床位数量
                available_beds = get_available_bed_count()
                
            except Exception as e:
                db.session.rollback()
                failed_count += 1
                print(f"❌ 注册失败: {str(e)}")
                continue
        
        print("\n" + "="*60)
        print("批量注册完成")
        print("="*60)
        print(f"成功注册: {registered_count} 名学生")
        print(f"失败: {failed_count} 名")
        print(f"剩余可用床位: {available_beds}")
        print("="*60)
        
        return registered_count

def test_dorm_change():
    """测试宿舍更换功能"""
    with app.app_context():
        print("\n" + "="*60)
        print("开始测试宿舍更换功能")
        print("="*60)
        
        # 获取所有已入住的学生
        students = Student.query.filter(Student.current_bed_id.isnot(None)).all()
        
        if len(students) < 2:
            print("⚠️  已入住学生数量不足，无法测试换宿功能")
            return
        
        # 随机选择一些学生进行换宿测试
        test_count = min(10, len(students) // 2)  # 最多测试10个，或学生数的一半
        test_students = random.sample(students, test_count)
        
        success_count = 0
        failed_count = 0
        
        for student in test_students:
            try:
                # 获取当前床位信息
                current_bed = student.current_bed
                if not current_bed:
                    continue
                
                current_dorm = current_bed.dorm
                current_building = current_dorm.building
                
                # 查找同性别且有可用床位的其他宿舍
                available_dorms = []
                for dorm in Dormitory.query.join(Building).filter(
                    Building.gender == student.gender,
                    Dormitory.id != current_dorm.id
                ).all():
                    available_beds = [bed for bed in dorm.beds 
                                    if bed.status == BedStatus.AVAILABLE.value]
                    if available_beds:
                        available_dorms.append((dorm, available_beds))
                
                if not available_dorms:
                    print(f"⚠️  学生 {student.name} 无法换宿：没有其他可用宿舍")
                    failed_count += 1
                    continue
                
                # 随机选择一个目标宿舍
                target_dorm, target_beds = random.choice(available_dorms)
                
                # 执行换宿
                # 1. 释放当前床位
                current_bed.status = BedStatus.AVAILABLE.value
                old_bed_id = student.current_bed_id
                student.current_bed_id = None
                
                # 2. 分配新床位
                new_bed = target_beds[0]
                new_bed.status = BedStatus.OCCUPIED.value
                student.current_bed_id = new_bed.id
                
                db.session.commit()
                
                # 验证换宿成功
                student.refresh()
                if student.current_bed_id == new_bed.id:
                    success_count += 1
                    print(f"✅ {student.name} 换宿成功: {current_building.name} {current_dorm.room_number} -> "
                          f"{target_dorm.building.name} {target_dorm.room_number}")
                else:
                    failed_count += 1
                    print(f"❌ {student.name} 换宿失败：验证失败")
                
            except Exception as e:
                db.session.rollback()
                failed_count += 1
                print(f"❌ {student.name} 换宿失败: {str(e)}")
        
        print("\n" + "="*60)
        print("宿舍更换测试完成")
        print("="*60)
        print(f"测试学生数: {test_count}")
        print(f"成功: {success_count}")
        print(f"失败: {failed_count}")
        print("="*60)

def show_statistics():
    """显示统计信息"""
    with app.app_context():
        print("\n" + "="*60)
        print("系统统计信息")
        print("="*60)
        
        total_students = Student.query.count()
        students_with_dorm = Student.query.filter(Student.current_bed_id.isnot(None)).count()
        total_beds = Bed.query.count()
        occupied_beds = Bed.query.filter_by(status=BedStatus.OCCUPIED.value).count()
        available_beds = Bed.query.filter_by(status=BedStatus.AVAILABLE.value).count()
        
        total_dorms = Dormitory.query.count()
        full_dorms = 0
        partial_dorms = 0
        empty_dorms = 0
        
        for dorm in Dormitory.query.all():
            occupied = len([bed for bed in dorm.beds if bed.status == BedStatus.OCCUPIED.value])
            if occupied == 0:
                empty_dorms += 1
            elif occupied == dorm.capacity:
                full_dorms += 1
            else:
                partial_dorms += 1
        
        print(f"学生总数: {total_students}")
        print(f"已入住学生: {students_with_dorm}")
        print(f"床位总数: {total_beds}")
        print(f"已占用床位: {occupied_beds} ({occupied_beds/total_beds*100:.1f}%)")
        print(f"可用床位: {available_beds} ({available_beds/total_beds*100:.1f}%)")
        print(f"\n宿舍总数: {total_dorms}")
        print(f"已满宿舍: {full_dorms}")
        print(f"部分入住: {partial_dorms}")
        print(f"空宿舍: {empty_dorms}")
        print("="*60)

def main():
    """主函数"""
    print("\n" + "="*60)
    print("批量注册学生并测试宿舍更换功能")
    print("="*60)
    
    # 1. 批量注册学生
    registered = batch_register_students()
    
    # 2. 显示统计信息
    show_statistics()
    
    # 3. 测试宿舍更换
    if registered and registered > 0:
        test_dorm_change()
        
        # 再次显示统计信息
        show_statistics()
    else:
        print("\n⚠️  没有成功注册学生，跳过换宿测试")

if __name__ == '__main__':
    main()

