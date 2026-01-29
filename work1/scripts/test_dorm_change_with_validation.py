#!/usr/bin/env python3
"""
测试宿舍更换功能，验证床位状态和入住人数的一致性
1. 注册学生直到只剩最后一个床位
2. 进行换宿测试
3. 检查并修复床位状态不一致的问题
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

def batch_register_until_one_left():
    """批量注册学生，直到只剩最后一个床位"""
    with app.app_context():
        print("="*60)
        print("开始批量注册学生（保留最后一个床位）")
        print("="*60)
        
        # 获取可用床位数量
        available_beds = get_available_bed_count()
        print(f"当前可用床位数量: {available_beds}")
        
        if available_beds <= 1:
            print(f"⚠️  可用床位数量为 {available_beds}，无需注册")
            return 0
        
        # 获取专业列表
        majors = Major.query.all()
        if not majors:
            print("⚠️  没有专业数据，请先创建专业")
            return 0
        
        # 生成姓名列表
        surnames = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴', 
                   '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗']
        given_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军',
                      '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞',
                      '平', '刚', '桂英', '建华', '文', '华', '红', '建国', '云', '鹏']
        
        registered_count = 0
        failed_count = 0
        
        # 批量注册，直到只剩最后一个床位
        while available_beds > 1:
            try:
                # 生成随机信息
                username = f"test_stu_{random.randint(100000, 999999)}"
                student_id = f"TS{random.randint(1000000, 9999999)}"
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
                        print(f"已注册 {registered_count} 名学生... (剩余床位: {available_beds - 1})")
                else:
                    # 如果没有分配到床位，删除刚创建的用户和学生
                    db.session.delete(student)
                    db.session.delete(user)
                    db.session.rollback()
                    print(f"⚠️  学生 {name} 无法分配到床位")
                    failed_count += 1
                    break
                
                db.session.commit()
                
                # 更新可用床位数量
                available_beds = get_available_bed_count()
                
                # 如果只剩一个床位，停止注册
                if available_beds <= 1:
                    break
                
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

def validate_dorm_consistency():
    """验证宿舍床位状态和入住人数的一致性"""
    with app.app_context():
        print("\n" + "="*60)
        print("验证宿舍床位状态一致性")
        print("="*60)
        
        issues = []
        
        # 检查每个宿舍
        for dorm in Dormitory.query.all():
            # 统计床位状态
            occupied_beds_count = len([bed for bed in dorm.beds if bed.status == BedStatus.OCCUPIED.value])
            available_beds_count = len([bed for bed in dorm.beds if bed.status == BedStatus.AVAILABLE.value])
            reserved_beds_count = len([bed for bed in dorm.beds if bed.status == BedStatus.RESERVED.value])
            total_beds_count = len(dorm.beds)
            
            # 验证床位总数
            if occupied_beds_count + available_beds_count + reserved_beds_count != total_beds_count:
                issues.append({
                    'dorm': dorm,
                    'type': '床位总数不匹配',
                    'details': f"已占用:{occupied_beds_count} + 可用:{available_beds_count} + 预留:{reserved_beds_count} != 总数:{total_beds_count}"
                })
            
            # 验证入住人数（通过学生记录统计）
            students_in_dorm = Student.query.filter_by(current_bed_id=None).join(Bed).filter(
                Bed.dorm_id == dorm.id,
                Bed.status == BedStatus.OCCUPIED.value
            ).count()
            
            # 更准确的方法：通过床位ID查找学生
            occupied_bed_ids = [bed.id for bed in dorm.beds if bed.status == BedStatus.OCCUPIED.value]
            actual_students_count = Student.query.filter(Student.current_bed_id.in_(occupied_bed_ids)).count()
            
            if actual_students_count != occupied_beds_count:
                issues.append({
                    'dorm': dorm,
                    'type': '入住人数不匹配',
                    'details': f"床位状态显示已占用:{occupied_beds_count}，但实际学生数:{actual_students_count}"
                })
            
            # 验证床位容量
            if total_beds_count != dorm.capacity:
                issues.append({
                    'dorm': dorm,
                    'type': '床位数量与容量不匹配',
                    'details': f"床位总数:{total_beds_count} != 宿舍容量:{dorm.capacity}"
                })
        
        # 检查孤立的学生记录（学生有床位ID但床位状态不对）
        all_students = Student.query.filter(Student.current_bed_id.isnot(None)).all()
        for student in all_students:
            bed = Bed.query.get(student.current_bed_id)
            if not bed:
                issues.append({
                    'dorm': None,
                    'type': '学生床位ID无效',
                    'details': f"学生 {student.name} (ID:{student.id}) 的床位ID {student.current_bed_id} 不存在"
                })
            elif bed.status != BedStatus.OCCUPIED.value:
                issues.append({
                    'dorm': bed.dorm,
                    'type': '学生床位状态不一致',
                    'details': f"学生 {student.name} 的床位状态为 {bed.status}，应该是 OCCUPIED"
                })
        
        # 检查孤立的已占用床位（床位状态为已占用但没有学生）
        all_occupied_beds = Bed.query.filter_by(status=BedStatus.OCCUPIED.value).all()
        for bed in all_occupied_beds:
            student = Student.query.filter_by(current_bed_id=bed.id).first()
            if not student:
                issues.append({
                    'dorm': bed.dorm,
                    'type': '床位状态异常',
                    'details': f"床位 {bed.dorm.building.name} {bed.dorm.room_number} {bed.bed_number}号床状态为已占用，但没有学生"
                })
        
        if issues:
            print(f"❌ 发现 {len(issues)} 个问题：\n")
            for i, issue in enumerate(issues, 1):
                dorm_info = f"{issue['dorm'].building.name} {issue['dorm'].room_number}" if issue['dorm'] else "未知"
                print(f"{i}. [{issue['type']}] {dorm_info}")
                print(f"   详情: {issue['details']}")
            return issues
        else:
            print("✅ 所有宿舍床位状态一致，未发现问题")
            return []

def fix_dorm_issues(issues):
    """修复发现的床位状态问题"""
    with app.app_context():
        print("\n" + "="*60)
        print("开始修复床位状态问题")
        print("="*60)
        
        fixed_count = 0
        
        for issue in issues:
            try:
                if issue['type'] == '学生床位状态不一致':
                    # 修复：将床位状态设置为已占用
                    student = Student.query.filter_by(current_bed_id=issue['dorm'].beds[0].id).first()
                    if student:
                        bed = Bed.query.get(student.current_bed_id)
                        if bed and bed.status != BedStatus.OCCUPIED.value:
                            bed.status = BedStatus.OCCUPIED.value
                            fixed_count += 1
                            print(f"✅ 修复: 学生 {student.name} 的床位状态已更新为已占用")
                
                elif issue['type'] == '床位状态异常':
                    # 修复：将没有学生的已占用床位释放
                    bed = None
                    for b in issue['dorm'].beds:
                        if b.status == BedStatus.OCCUPIED.value and not Student.query.filter_by(current_bed_id=b.id).first():
                            bed = b
                            break
                    if bed:
                        bed.status = BedStatus.AVAILABLE.value
                        fixed_count += 1
                        print(f"✅ 修复: {issue['dorm'].building.name} {issue['dorm'].room_number} {bed.bed_number}号床已释放")
                
                elif issue['type'] == '学生床位ID无效':
                    # 修复：清除无效的床位ID
                    student_id = int(issue['details'].split('ID:')[1].split(')')[0])
                    student = Student.query.get(student_id)
                    if student:
                        student.current_bed_id = None
                        fixed_count += 1
                        print(f"✅ 修复: 学生 {student.name} 的无效床位ID已清除")
                
            except Exception as e:
                print(f"❌ 修复失败: {str(e)}")
                continue
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\n✅ 共修复 {fixed_count} 个问题")
        else:
            print("\n⚠️  没有需要修复的问题")
        
        return fixed_count

def test_dorm_change_with_validation():
    """测试宿舍更换功能并验证一致性"""
    with app.app_context():
        print("\n" + "="*60)
        print("开始测试宿舍更换功能（只剩最后一个床位）")
        print("="*60)
        
        # 获取所有已入住的学生
        students = Student.query.filter(Student.current_bed_id.isnot(None)).all()
        
        if len(students) < 2:
            print("⚠️  已入住学生数量不足，无法测试换宿功能")
            return
        
        # 获取最后一个可用床位
        last_available_bed = Bed.query.filter_by(status=BedStatus.AVAILABLE.value).first()
        if not last_available_bed:
            print("⚠️  没有可用床位，无法测试换宿")
            return
        
        print(f"最后一个可用床位: {last_available_bed.dorm.building.name} {last_available_bed.dorm.room_number} {last_available_bed.bed_number}号床")
        
        # 选择一个学生进行换宿测试
        test_student = random.choice(students)
        
        try:
            # 获取当前床位信息
            current_bed = test_student.current_bed
            if not current_bed:
                print("⚠️  学生没有当前床位")
                return
            
            current_dorm = current_bed.dorm
            current_building = current_dorm.building
            
            print(f"\n测试学生: {test_student.name}")
            print(f"当前宿舍: {current_building.name} {current_dorm.room_number}")
            print(f"目标宿舍: {last_available_bed.dorm.building.name} {last_available_bed.dorm.room_number}")
            
            # 记录换宿前的状态
            before_occupied = current_dorm.occupied_count
            before_available = len(current_dorm.available_beds)
            target_before_occupied = last_available_bed.dorm.occupied_count
            target_before_available = len(last_available_bed.dorm.available_beds)
            
            # 执行换宿
            # 1. 释放当前床位
            current_bed.status = BedStatus.AVAILABLE.value
            old_bed_id = test_student.current_bed_id
            test_student.current_bed_id = None
            
            # 2. 分配新床位（最后一个可用床位）
            last_available_bed.status = BedStatus.OCCUPIED.value
            test_student.current_bed_id = last_available_bed.id
            
            db.session.commit()
            
            # 刷新对象
            db.session.refresh(current_dorm)
            db.session.refresh(last_available_bed.dorm)
            
            # 验证换宿后的状态
            after_occupied = current_dorm.occupied_count
            after_available = len(current_dorm.available_beds)
            target_after_occupied = last_available_bed.dorm.occupied_count
            target_after_available = len(last_available_bed.dorm.available_beds)
            
            print(f"\n换宿前状态:")
            print(f"  原宿舍: 已占用 {before_occupied}, 可用 {before_available}")
            print(f"  目标宿舍: 已占用 {target_before_occupied}, 可用 {target_before_available}")
            
            print(f"\n换宿后状态:")
            print(f"  原宿舍: 已占用 {after_occupied}, 可用 {after_available}")
            print(f"  目标宿舍: 已占用 {target_after_occupied}, 可用 {target_after_available}")
            
            # 验证状态变化
            success = True
            if after_occupied != before_occupied - 1:
                print(f"❌ 原宿舍入住人数错误: 应该是 {before_occupied - 1}，实际是 {after_occupied}")
                success = False
            if after_available != before_available + 1:
                print(f"❌ 原宿舍可用床位错误: 应该是 {before_available + 1}，实际是 {after_available}")
                success = False
            if target_after_occupied != target_before_occupied + 1:
                print(f"❌ 目标宿舍入住人数错误: 应该是 {target_before_occupied + 1}，实际是 {target_after_occupied}")
                success = False
            if target_after_available != target_before_available - 1:
                print(f"❌ 目标宿舍可用床位错误: 应该是 {target_before_available - 1}，实际是 {target_after_available}")
                success = False
            
            if success:
                print("\n✅ 换宿成功，床位状态和入住人数一致")
            else:
                print("\n❌ 换宿后状态不一致，需要修复")
            
            return success
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 换宿测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

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
    print("测试宿舍更换功能并验证床位状态一致性")
    print("="*60)
    
    # 1. 批量注册学生，直到只剩最后一个床位
    registered = batch_register_until_one_left()
    
    # 2. 显示统计信息
    show_statistics()
    
    # 3. 验证床位状态一致性（换宿前）
    print("\n【换宿前验证】")
    issues_before = validate_dorm_consistency()
    
    # 4. 如果有问题，先修复
    if issues_before:
        fix_dorm_issues(issues_before)
        # 再次验证
        issues_after_fix = validate_dorm_consistency()
        if issues_after_fix:
            print("⚠️  修复后仍有问题，请检查")
    
    # 5. 测试宿舍更换
    if registered and registered > 0:
        test_success = test_dorm_change_with_validation()
        
        # 6. 验证床位状态一致性（换宿后）
        print("\n【换宿后验证】")
        issues_after = validate_dorm_consistency()
        
        # 7. 如果有问题，修复
        if issues_after:
            fixed = fix_dorm_issues(issues_after)
            if fixed > 0:
                # 再次验证
                final_issues = validate_dorm_consistency()
                if not final_issues:
                    print("\n✅ 所有问题已修复，床位状态现在一致")
        
        # 8. 最终统计
        show_statistics()
    else:
        print("\n⚠️  没有成功注册学生，跳过换宿测试")

if __name__ == '__main__':
    main()

