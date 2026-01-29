from start import app, db
from models.database import db, UserRole, BedStatus, ApplicationStatus
from models.user import User, Student
from models.dormitory import Building, Dormitory, Bed
from models.application import SelectionBatch
from models.system import Announcement
from models.user import Major
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import string

def init_database():
    """初始化数据库"""
    with app.app_context():
        # 删除并重建所有表
        db.drop_all()
        db.create_all()
        
        print("开始初始化数据...")
        
        # 1. 创建管理员账户
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role=UserRole.ADMIN.value
        )
        db.session.add(admin_user)
        
        # 宿管账户
        manager_user = User(
            username='manager',
            password_hash=generate_password_hash('manager123'),
            role=UserRole.DORM_MANAGER.value
        )
        db.session.add(manager_user)
        
        # 2. 创建专业数据
        departments = {
            '计算机学院': ['计算机科学与技术', '软件工程', '人工智能', '数据科学', '网络工程', 
                       '信息安全', '物联网工程', '数字媒体技术'],
            '工程学院': ['机械工程', '土木工程', '化学工程与工艺', '环境工程', '电气工程及其自动化',
                     '自动化', '通信工程', '生物医学工程', '材料科学与工程'],
            '理学院': ['数学与应用数学', '物理学', '化学', '生物科学', '统计学', '应用物理学'],
            '商学院': ['经济学', '金融学', '国际经济与贸易', '工商管理', '市场营销', 
                    '会计学', '财务管理', '人力资源管理', '电子商务', '物流管理'],
            '文学院': ['汉语言文学', '英语', '日语', '新闻学', '广告学', '历史学', '哲学'],
            '教育学院': ['教育学', '心理学', '学前教育', '小学教育', '体育教育'],
            '艺术学院': ['音乐学', '美术学', '设计学类', '视觉传达设计', '环境设计'],
            '医学院': ['临床医学', '口腔医学', '护理学', '药学', '中医学', '中药学']
        }
        
        major_code = 1
        for dept, major_names in departments.items():
            for major_name in major_names:
                major = Major(
                    name=major_name,
                    code=str(major_code).zfill(3),
                    department=dept
                )
                db.session.add(major)
                major_code += 1
        
        # 3. 创建楼栋数据
        building_data = [
            # 男生宿舍区（东区）
            {'name': '东1栋', 'gender': '男', 'floors': 6, 'location': '东区靠近图书馆', 
             'facilities': '24小时热水,空调,独立卫浴,洗衣房,自习室'},
            {'name': '东2栋', 'gender': '男', 'floors': 6, 'location': '东区靠近第一食堂',
             'facilities': '24小时热水,空调,独立卫浴,洗衣房'},
            {'name': '东3栋', 'gender': '男', 'floors': 6, 'location': '东区靠近体育馆',
             'facilities': '24小时热水,空调,公共卫浴,洗衣房'},
            {'name': '东4栋', 'gender': '男', 'floors': 5, 'location': '东区靠近教学楼',
             'facilities': '24小时热水,空调,独立卫浴'},
            {'name': '东5栋', 'gender': '男', 'floors': 5, 'location': '东区中心位置',
             'facilities': '24小时热水,空调,公共卫浴'},
            
            # 女生宿舍区（西区）
            {'name': '西1栋', 'gender': '女', 'floors': 6, 'location': '西区靠近图书馆',
             'facilities': '24小时热水,空调,独立卫浴,洗衣房,自习室,健身房'},
            {'name': '西2栋', 'gender': '女', 'floors': 6, 'location': '西区靠近第二食堂',
             'facilities': '24小时热水,空调,独立卫浴,洗衣房,便利店'},
            {'name': '西3栋', 'gender': '女', 'floors': 6, 'location': '西区靠近艺术楼',
             'facilities': '24小时热水,空调,独立卫浴,洗衣房'},
            {'name': '西4栋', 'gender': '女', 'floors': 5, 'location': '西区靠近医务室',
             'facilities': '24小时热水,空调,公共卫浴,洗衣房'},
            {'name': '西5栋', 'gender': '女', 'floors': 5, 'location': '西区中心位置',
             'facilities': '24小时热水,空调,公共卫浴'},
            
            # 新建宿舍区（南区，男女混住楼栋但楼层分开）
            {'name': '南1栋', 'gender': '男', 'floors': 8, 'location': '南区新建楼栋',
             'facilities': '24小时热水,中央空调,独立卫浴,电梯,洗衣房,自习室,健身房,咖啡厅'},
            {'name': '南2栋', 'gender': '女', 'floors': 8, 'location': '南区新建楼栋',
             'facilities': '24小时热水,中央空调,独立卫浴,电梯,洗衣房,自习室,健身房,咖啡厅'},
        ]
        
        for building_info in building_data:
            building = Building(
                name=building_info['name'],
                gender=building_info['gender'],
                total_floors=building_info['floors'],
                location=building_info['location'],
                facilities=building_info['facilities'],
                description=f"{building_info['name']}是{building_info['gender']}生宿舍楼，共{building_info['floors']}层"
            )
            db.session.add(building)
            db.session.flush()
            
            # 4. 为每栋楼创建宿舍房间
            room_configs = {
                1: {'capacity': 2, 'type': '豪华双人间', 'rent': 2000, 'has_balcony': True},
                2: {'capacity': 2, 'type': '豪华双人间', 'rent': 2000, 'has_balcony': True},
                3: {'capacity': 4, 'type': '标准四人间', 'rent': 1200, 'has_balcony': True},
                4: {'capacity': 4, 'type': '标准四人间', 'rent': 1200, 'has_balcony': False},
                5: {'capacity': 6, 'type': '经济六人间', 'rent': 800, 'has_balcony': False},
                6: {'capacity': 6, 'type': '经济六人间', 'rent': 800, 'has_balcony': False},
            }
            
            # 新建楼栋的特殊配置
            if '南' in building_info['name']:
                room_configs.update({
                    7: {'capacity': 2, 'type': '豪华双人间', 'rent': 2500, 'has_balcony': True},
                    8: {'capacity': 2, 'type': '豪华双人间', 'rent': 2500, 'has_balcony': True},
                })
            
            for floor in range(1, building_info['floors'] + 1):
                config = room_configs.get(floor, room_configs[3])  # 默认4人间
                
                # 每层8个房间
                for room_num in range(1, 9):
                    room_number = f"{floor}{str(room_num).zfill(2)}"
                    
                    # 计算朝向
                    if room_num <= 4:
                        orientation = '南向'
                    else:
                        orientation = '北向'
                    
                    dorm = Dormitory(
                        building_id=building.id,
                        room_number=room_number,
                        floor=floor,
                        capacity=config['capacity'],
                        room_type=config['type'],
                        has_ac=True,
                        has_bathroom=True if config['capacity'] <= 4 else False,
                        has_balcony=config['has_balcony'],
                        has_water_heater=True,
                        monthly_rent=config['rent'],
                        area=20 + config['capacity'] * 3,  # 基础面积+每人3平米
                        orientation=orientation
                    )
                    db.session.add(dorm)
                    db.session.flush()
                    
                    # 5. 为每个宿舍创建床位
                    positions = {
                        2: ['靠窗上铺', '靠门下铺'],
                        4: ['靠窗上铺', '靠窗下铺', '靠门上铺', '靠门下铺'],
                        6: ['靠窗上铺', '靠窗中铺', '靠窗下铺', '靠门上铺', '靠门中铺', '靠门下铺']
                    }
                    
                    for bed_num, position in enumerate(positions.get(config['capacity'], positions[4]), 1):
                        bed = Bed(
                            dorm_id=dorm.id,
                            bed_number=bed_num,
                            position=position,
                            status=BedStatus.AVAILABLE.value
                        )
                        db.session.add(bed)
        
        # 6. 创建选宿批次
        current_year = datetime.now().year
        batches = [
            {
                'name': f'{current_year}年秋季新生选宿（第一批）',
                'grade': current_year,
                'start_time': datetime.now() - timedelta(days=7),
                'end_time': datetime.now() + timedelta(days=7),
                'description': '大一新生第一批选宿，优先开放豪华双人间和标准四人间'
            },
            {
                'name': f'{current_year}年秋季新生选宿（第二批）',
                'grade': current_year,
                'start_time': datetime.now() + timedelta(days=8),
                'end_time': datetime.now() + timedelta(days=14),
                'description': '大一新生第二批选宿，开放所有房型'
            },
            {
                'name': f'{current_year}年春季换宿',
                'grade': current_year - 1,
                'start_time': datetime.now() + timedelta(days=30),
                'end_time': datetime.now() + timedelta(days=37),
                'description': '在校生换宿申请'
            }
        ]
        
        for batch_data in batches:
            batch = SelectionBatch(
                name=batch_data['name'],
                grade=batch_data['grade'],
                start_time=batch_data['start_time'],
                end_time=batch_data['end_time'],
                is_active=True,
                max_applications=1,
                description=batch_data['description']
            )
            db.session.add(batch)
        
        # 7. 创建公告
        announcements = [
            {
                'title': '2024年秋季新生宿舍选择指南',
                'content': '''
                欢迎新同学！以下是宿舍选择的详细指南：
                
                1. 选宿时间：请在规定时间内完成选宿
                2. 房型介绍：
                   - 豪华双人间：独立卫浴、阳台、空调、2000元/月
                   - 标准四人间：独立/公共卫浴、空调、1200元/月
                   - 经济六人间：公共卫浴、空调、800元/月
                3. 选宿流程：登录系统 -> 浏览宿舍 -> 选择床位 -> 提交申请 -> 等待审核
                4. 组团选宿：可创建或加入团队，与朋友一起选择同一宿舍
                
                如有疑问，请联系宿管中心：xxx-xxxx-xxxx
                ''',
                'category': '选宿指南',
                'priority': 10,
                'expire_at': datetime.now() + timedelta(days=30)
            },
            {
                'title': '宿舍管理规定',
                'content': '''
                为营造良好的住宿环境，请遵守以下规定：
                
                1. 作息时间：晚11点后请保持安静
                2. 卫生要求：保持宿舍整洁，垃圾及时清理
                3. 安全规定：禁止使用大功率电器，注意防火防盗
                4. 访客管理：访客需在楼下登记，晚10点前离开
                5. 公共设施：爱护公共财物，节约用水用电
                
                违反规定将受到相应处罚。
                ''',
                'category': '管理规定',
                'priority': 5,
                'expire_at': datetime.now() + timedelta(days=365)
            },
            {
                'title': '关于开放南区新宿舍楼的通知',
                'content': '''
                好消息！南区新建宿舍楼现已全面开放！
                
                南1栋（男生）、南2栋（女生）配备最新设施：
                - 中央空调系统
                - 电梯直达各层
                - 每层设有自习室
                - 一楼设有健身房和咖啡厅
                - 24小时热水供应
                - 高速WiFi全覆盖
                
                欢迎同学们申请入住！
                ''',
                'category': '重要通知',
                'priority': 8,
                'expire_at': datetime.now() + timedelta(days=15)
            }
        ]
        
        for ann_data in announcements:
            announcement = Announcement(
                title=ann_data['title'],
                content=ann_data['content'],
                category=ann_data['category'],
                priority=ann_data['priority'],
                created_by=admin_user.id,
                expire_at=ann_data['expire_at']
            )
            db.session.add(announcement)
        
        # 8. 创建示例学生账户
        majors_list = Major.query.all()
        
        for i in range(10):
            # 创建用户账号
            username = f'student{i+1}'
            user = User(
                username=username,
                password_hash=generate_password_hash('123456'),
                role=UserRole.STUDENT.value
            )
            db.session.add(user)
            db.session.flush()
            
            # 创建学生信息
            gender = '男' if i < 5 else '女'
            student = Student(
                user_id=user.id,
                student_id=f'2024{str(i+1).zfill(6)}',
                name=f'测试学生{i+1}',
                id_card=f'44030019990{str(i+1).zfill(2)}0000',
                gender=gender,
                phone=f'1380000{str(i+1).zfill(4)}',
                email=f'student{i+1}@example.com',
                major_id=random.choice(majors_list).id,
                grade=2024,
                # 生活习惯随机设置
                sleep_time=random.choice(['早睡(22:00前)', '正常(22:00-24:00)', '晚睡(24:00后)']),
                wake_time=random.choice(['早起(7:00前)', '正常(7:00-8:00)', '晚起(8:00后)']),
                quietness=random.randint(1, 5),
                cleanliness=random.randint(1, 5),
                hobbies='运动,音乐,阅读'
            )
            db.session.add(student)
        
        # 提交所有数据
        db.session.commit()
        
        print("数据库初始化完成！")
        print("\n管理员账户:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("\n宿管账户:")
        print("  用户名: manager")
        print("  密码: manager123")
        print("\n示例学生账户:")
        print("  用户名: student1 到 student10")
        print("  密码: 123456")

if __name__ == '__main__':
    init_database()