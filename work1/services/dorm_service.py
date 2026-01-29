from models.database import db, UserRole, BedStatus, ApplicationStatus
from models.user import User, Student
from models.dormitory import Dormitory, Bed
from models.application import DormApplication
from datetime import datetime
from werkzeug.security import generate_password_hash

class DormService:#宿舍审批
    def get_dashboard_statistics(self):
        """获取仪表盘统计数据"""
        total_students = Student.query.count()
        total_beds = Bed.query.count()
        occupied_beds = Bed.query.filter_by(status=BedStatus.OCCUPIED.value).count()
        pending_applications = DormApplication.query.filter_by(
            status=ApplicationStatus.PENDING.value
        ).count()
        
        return {
            'total_students': total_students,
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'occupancy_rate': (occupied_beds / total_beds * 100) if total_beds > 0 else 0,
            'pending_applications': pending_applications
        }
        
    def approve_application(self, application_id, admin_id):
        """审批通过宿舍申请"""
        application = DormApplication.query.get_or_404(application_id)
        if application.status != ApplicationStatus.PENDING.value:
            raise ValueError('该申请已被处理')
            
        # 检查床位可用性
        if application.application_type == 'change':
            target_dorm = Dormitory.query.get(application.target_dorm_id)
            available_beds = [bed for bed in target_dorm.beds 
                            if bed.status == BedStatus.AVAILABLE.value]
            if not available_beds:
                raise ValueError('目标宿舍暂无空床')
                
            student = Student.query.get(application.student_id)
            # 释放原床位
            if student.current_bed:
                student.current_bed.status = BedStatus.AVAILABLE.value
                
            # 分配新床位
            new_bed = available_beds[0]
            new_bed.status = BedStatus.OCCUPIED.value
            student.current_bed_id = new_bed.id
            
        application.status = ApplicationStatus.APPROVED.value
        application.processed_at = datetime.now()
        application.processed_by = admin_id
        
        try:
            db.session.commit()
            return {'success': True, 'message': '申请已审批通过'}
        except Exception as e:
            db.session.rollback()
            raise e
            
    def reject_application(self, application_id, admin_id):
        """拒绝宿舍申请"""
        application = DormApplication.query.get_or_404(application_id)
        if application.status != ApplicationStatus.PENDING.value:
            raise ValueError('该申请已被处理')
            
        application.status = ApplicationStatus.REJECTED.value
        application.processed_at = datetime.now()
        application.processed_by = admin_id
        
        try:
            db.session.commit()
            return {'success': True, 'message': '申请已被拒绝'}
        except Exception as e:
            db.session.rollback()
            raise e