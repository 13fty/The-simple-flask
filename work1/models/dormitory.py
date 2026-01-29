from .database import db, BedStatus

class Building(db.Model):
    __tablename__ = 'buildings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    total_floors = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100))  # 位置描述
    facilities = db.Column(db.Text)  # 设施说明
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))

class Dormitory(db.Model):
    __tablename__ = 'dormitories'
    id = db.Column(db.Integer, primary_key=True)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'))
    room_number = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(20))  # 标准间/豪华间
    
    # 设施
    has_ac = db.Column(db.Boolean, default=True)
    has_bathroom = db.Column(db.Boolean, default=True)
    has_balcony = db.Column(db.Boolean, default=False)
    has_water_heater = db.Column(db.Boolean, default=True)
    
    monthly_rent = db.Column(db.Float)  # 月租金
    area = db.Column(db.Float)  # 面积
    orientation = db.Column(db.String(20))  # 朝向
    
    building = db.relationship('Building', backref='dormitories')
    
    @property
    def available_beds(self):
        return [bed for bed in self.beds if bed.status == BedStatus.AVAILABLE.value]
    
    @property
    def occupied_count(self):
        return len([bed for bed in self.beds if bed.status == BedStatus.OCCUPIED.value])

class Bed(db.Model):
    __tablename__ = 'beds'
    id = db.Column(db.Integer, primary_key=True)
    dorm_id = db.Column(db.Integer, db.ForeignKey('dormitories.id'), nullable=False)
    bed_number = db.Column(db.Integer, nullable=False)
    position = db.Column(db.String(20))  # 上铺/下铺/靠窗/靠门
    status = db.Column(db.String(20), default=BedStatus.AVAILABLE.value)
    
    dorm = db.relationship('Dormitory', backref='beds')
