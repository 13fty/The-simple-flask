# 项目运行环境要求

## 操作系统
- 推荐：macOS 14+/Windows 11/Ubuntu 22.04 及以上版本
- 需要具备 SQLite3（macOS 与大部分 Linux 系统自带）

## 必备软件
- Python 3.9（使用 `python3 --version` 确认）
- pip（Python 自带，若缺少使用 `python3 -m ensurepip --upgrade` 安装）
- Git（用于克隆和版本管理，可选）

## Python 依赖（`pip install -r requirements.txt`）
- Flask==2.3.3
- Flask-SQLAlchemy==3.0.5
- Flask-Login==0.6.3
- Werkzeug==2.3.7

## 可选工具
- `python3 -m pip install pytest`：运行单元测试
- VS Code / PyCharm 等 IDE：方便调试与开发

## 初始化步骤
1. `python3 -m pip install -r requirements.txt`
2. `python3 init_db.py`（首次运行初始化数据库）
3. `python3 start.py` 启动服务，访问 `http://localhost:5001`
