#!/usr/bin/env python3
"""
添加宿舍数据脚本（简化版）
按照男女，4人间和6人间，1-10楼创建宿舍
不包含床位位置、月租金、设施配置等详细信息
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from start import app, db
from models.dormitory import Building, Dormitory, Bed
from models.database import BedStatus

def add_dormitories():
    """添加宿舍数据"""
    with app.app_context():
        print("开始创建宿舍数据...")
        
        # 检查是否已有楼栋
        existing_buildings = Building.query.count()
        if existing_buildings > 0:
            print(f"⚠️  发现已有 {existing_buildings} 栋楼，是否要删除后重建？")
            response = input("输入 'yes' 删除现有楼栋并重建，或直接回车跳过: ").strip().lower()
            if response == 'yes':
                print("删除现有楼栋和宿舍数据...")
                # 删除所有床位
                Bed.query.delete()
                # 删除所有宿舍
                Dormitory.query.delete()
                # 删除所有楼栋
                Building.query.delete()
                db.session.commit()
                print("✅ 已删除现有数据")
            else:
                print("保留现有数据，只创建新楼栋...")
        
        # 创建10栋宿舍楼（1-10号）
        buildings = []
        for i in range(1, 11):
            # 奇数号楼为男生楼，偶数号楼为女生楼
            gender = '男' if i % 2 == 1 else '女'
            building_name = f'{i}号宿舍楼'
            
            # 检查是否已存在
            existing = Building.query.filter_by(name=building_name).first()
            if existing:
                print(f"⚠️  {building_name} 已存在，跳过...")
                buildings.append(existing)
                continue
            
            building = Building(
                name=building_name,
                gender=gender,
                total_floors=10,  # 1-10楼
                location=f'校园{i}号区域',
                facilities='',  # 不设置设施
                description=f'{building_name}是{gender}生宿舍楼，共10层'
            )
            db.session.add(building)
            buildings.append(building)
            print(f"✅ 创建楼栋: {building_name} ({gender}生)")
        
        db.session.flush()
        
        # 为每栋楼创建宿舍
        total_dorms = 0
        total_beds = 0
        
        for building in buildings:
            print(f"\n正在为 {building.name} 创建宿舍...")
            
            # 为每层创建房间
            for floor in range(1, 11):  # 1-10楼
                # 每层创建10个房间，5个4人间，5个6人间
                for room_num in range(1, 11):
                    # 前5个为4人间，后5个为6人间
                    if room_num <= 5:
                        capacity = 4
                        room_type = '标准四人间'
                    else:
                        capacity = 6
                        room_type = '经济六人间'
                    
                    room_number = f"{floor:02d}{room_num:02d}"
                    
                    # 检查是否已存在
                    existing_dorm = Dormitory.query.filter_by(
                        building_id=building.id,
                        room_number=room_number
                    ).first()
                    
                    if existing_dorm:
                        continue  # 跳过已存在的房间
                    
                    # 计算朝向（奇数号房间南向，偶数号房间北向）
                    orientation = '南向' if room_num % 2 == 1 else '北向'
                    
                    # 简化版：不设置月租金、面积和详细设施
                    dorm = Dormitory(
                        building_id=building.id,
                        room_number=room_number,
                        floor=floor,
                        capacity=capacity,
                        room_type=room_type,
                        orientation=orientation
                        # 其他字段使用数据库默认值或留空
                    )
                    db.session.add(dorm)
                    db.session.flush()
                    total_dorms += 1
                    
                    # 为每个宿舍创建床位（简化版：只设置编号，不设置位置）
                    for bed_num in range(1, capacity + 1):
                        bed = Bed(
                            dorm_id=dorm.id,
                            bed_number=bed_num,
                            position=None,  # 不设置床位位置
                            status=BedStatus.AVAILABLE.value
                        )
                        db.session.add(bed)
                        total_beds += 1
            
            print(f"✅ {building.name} 完成: 100个宿舍")
        
        # 提交所有更改
        db.session.commit()
        
        print("\n" + "="*50)
        print("✅ 宿舍数据创建完成！")
        print("="*50)
        print(f"楼栋数量: {len(buildings)} 栋")
        print(f"宿舍总数: {total_dorms} 间")
        print(f"床位总数: {total_beds} 个")
        print("\n分布情况:")
        print("- 每栋楼: 10层（1-10楼）")
        print("- 每层: 10个房间（5个4人间 + 5个6人间）")
        print("- 每栋楼: 100个宿舍")
        print("- 男生楼: 1, 3, 5, 7, 9号")
        print("- 女生楼: 2, 4, 6, 8, 10号")
        print("="*50)

if __name__ == '__main__':
    add_dormitories()
