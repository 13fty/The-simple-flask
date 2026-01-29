# 宿舍管理系统

一个基于Flask的现代化宿舍管理系统，支持学生选宿、管理员审核、室友匹配等功能。

## 项目结构

```
work1/
├── start.py                # 主应用入口文件
├── init_db.py             # 数据库初始化脚本
├── requirements.txt        # 依赖包
├── README.md              # 项目说明
├── .gitignore             # Git忽略文件
│
├── config/                # 配置文件
│   ├── __init__.py
│   └── settings.py        # 应用配置
│
├── models/                # 数据模型
│   ├── __init__.py
│   ├── database.py        # 数据库配置和枚举
│   ├── user.py           # 用户相关模型
│   ├── dormitory.py      # 宿舍相关模型
│   ├── application.py    # 申请相关模型
│   ├── system.py         # 系统相关模型
│   └── audit.py          # 审计日志模型
│
├── routes/               # 路由模块
│   ├── __init__.py
│   ├── auth.py          # 认证路由
│   ├── main.py          # 主要路由
│   ├── student.py       # 学生路由
│   ├── dorm.py          # 宿舍路由
│   └── admin.py         # 管理员路由
│
├── templates/           # 模板文件
│   ├── base.html        # 基础模板
│   ├── index.html       # 首页
│   ├── auth/            # 认证相关模板
│   ├── student/         # 学生相关模板
│   ├── admin/           # 管理员相关模板
│   ├── dorms/           # 宿舍相关模板
│   └── errors/          # 错误页面模板
│
├── static/              # 静态文件
│   ├── css/
│   │   └── style.css    # 自定义样式
│   ├── js/
│   │   └── main.js      # 主要JavaScript
│   └── images/          # 图片资源
│
├── scripts/             # 工具脚本
│   ├── add_dormitories.py      # 添加宿舍数据脚本
│   └── migrate_add_fields.py   # 数据库迁移脚本
│
├── docs/                # 文档目录
│   ├── IMPROVEMENTS.md  # 改进建议文档
│   ├── paper.md         # 论文文档
│   └── remind.md        # 提醒文档
│
├── utils/               # 工具函数
│   └── error_handlers.py # 错误处理
│
├── tests/               # 测试文件
│   └── test_dorm_system.py
│
└── archive/             # 归档文件（未使用的旧文件）
    ├── app.py
    ├── create_db.py
    ├── run.py
    └── ...
```

## 功能特性

### 学生功能
- 用户注册/登录
- 浏览宿舍（支持筛选）
- 选择宿舍申请
- 查看申请状态
- 室友匹配
- 团队组团

### 管理员功能
- 审核学生申请
- 查看系统统计
- 管理宿舍信息
- 发布公告

### 系统特性
- 响应式设计
- 现代化UI
- 数据统计
- 权限控制

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库（首次运行）
```bash
python init_db.py
```

### 3. 添加宿舍数据（可选）
```bash
python scripts/add_dormitories.py
```

### 4. 运行应用
```bash
python start.py
```

### 5. 访问系统
打开浏览器访问：`http://localhost:5001`

## 默认账号

### 管理员账号
- 用户名：`admin`
- 密码：`admin123`

## 数据库

系统使用SQLite数据库，首次运行会自动创建：
- 10栋宿舍楼（每栋10层）
- 1000间宿舍（4人间/6人间）
- 管理员账号
- 专业数据

## 技术栈

- **后端**：Flask, SQLAlchemy, Flask-Login
- **前端**：Bootstrap 5, Bootstrap Icons
- **数据库**：SQLite
- **模板引擎**：Jinja2

## 开发说明

### 模块化设计
- `config/`：配置文件
- `models/`：数据模型
- `routes/`：路由处理
- `templates/`：HTML模板
- `static/`：静态资源
- `scripts/`：工具脚本

### 工具脚本

#### 添加宿舍数据
```bash
python scripts/add_dormitories.py
```

#### 数据库迁移
```bash
python scripts/migrate_add_fields.py
```

## 许可证

MIT License
