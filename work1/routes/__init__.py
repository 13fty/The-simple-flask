# 路由模块

from .dorm import dorm_bp
from .main import main_bp
from .auth import auth_bp
from .admin import admin_bp

__all__ = ['dorm_bp', 'main_bp', 'auth_bp', 'admin_bp']
