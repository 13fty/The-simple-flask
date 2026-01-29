import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask, render_template
from models.database import db
from models.audit import AuditLog

def configure_logging(app):
    """配置日志系统"""
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # 配置文件日志
    file_handler = RotatingFileHandler(
        'logs/dorm_system.log',
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('宿舍管理系统启动')

def configure_error_handlers(app):
    """配置错误处理"""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
        
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
        
    @app.after_request
    def after_request(response):
        """请求后处理"""
        try:
            # 记录用户操作
            if hasattr(response, '_status_code') and response._status_code == 200:
                endpoint = request.endpoint
                if endpoint and not endpoint.startswith('static'):
                    AuditLog.log_action(
                        user_id=current_user.id if not current_user.is_anonymous else None,
                        action=endpoint,
                        detail=str(request.form if request.form else request.args),
                        ip_address=request.remote_addr
                    )
        except Exception as e:
            app.logger.error(f'Error logging request: {str(e)}')
            
        return response