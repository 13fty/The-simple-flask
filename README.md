🏫 宿舍管理系统（Dormitory Management System）

一个 基于 Flask 的现代化宿舍管理系统，面向高校新生宿舍分配与管理场景设计，支持学生在线选宿、室友匹配、管理员审核与系统统计，具备清晰的模块化结构，适合作为 课程设计 / 毕业设计 / Flask 实战项目。

⸻

✨ 项目亮点
	•	学生自主选宿 + 管理员审核的完整流程
	•	多维度宿舍与室友匹配逻辑
	•	清晰的 MVC 分层结构，易于二次开发
	•	现代化 UI（Bootstrap 5）+ 响应式设计
	•	适合教学、学习和实际部署的工程结构

⸻

📂 项目结构

My_bysj/
├── start.py                # 应用启动入口
├── init_db.py              # 数据库初始化脚本
├── requirements.txt        # Python 依赖
├── README.md               # 项目说明文档
├── .gitignore
│
├── config/                 # 配置模块
│   └── settings.py
│
├── models/                 # ORM 数据模型
│   ├── database.py         # 数据库连接与枚举定义
│   ├── user.py             # 用户模型
│   ├── dormitory.py        # 宿舍模型
│   ├── application.py      # 申请记录模型
│   ├── system.py           # 系统参数模型
│   └── audit.py            # 审计日志模型
│
├── routes/                 # 路由控制层
│   ├── auth.py             # 登录 / 注册
│   ├── student.py          # 学生功能
│   ├── dorm.py             # 宿舍相关接口
│   ├── admin.py            # 管理员功能
│   └── main.py             # 通用页面
│
├── templates/              # Jinja2 模板
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── student/
│   ├── admin/
│   ├── dorms/
│   └── errors/
│
├── static/                 # 静态资源
│   ├── css/style.css
│   ├── js/main.js
│   └── images/
│
├── scripts/                # 运维 / 数据脚本
│   ├── add_dormitories.py  # 初始化宿舍数据
│   └── migrate_add_fields.py
│
├── utils/                  # 工具模块
│   └── error_handlers.py
│
├── tests/                  # 单元测试
│   └── test_dorm_system.py
│
└── docs/                   # 文档
    ├── paper.md            # 论文文档
    ├── IMPROVEMENTS.md     # 改进方向
    └── remind.md


⸻

👤 功能介绍

学生端
	•	用户注册 / 登录
	•	浏览宿舍（支持条件筛选）
	•	提交宿舍申请
	•	查看审核状态
	•	室友匹配与组团申请

管理员端
	•	学生申请审核
	•	宿舍信息管理
	•	系统数据统计
	•	公告发布

系统特性
	•	权限控制（学生 / 管理员）
	•	审计日志记录
	•	模块化、低耦合设计
	•	响应式布局，支持移动端

⸻

🚀 快速开始

1️⃣ 克隆项目

git clone https://github.com/yourname/your-repo.git
cd work1

2️⃣ 安装依赖

pip install -r requirements.txt

3️⃣ 初始化数据库（首次运行）

python init_db.py

4️⃣ （可选）生成宿舍数据

python scripts/add_dormitories.py

5️⃣ 启动服务

python start.py

访问地址：

http://127.0.0.1:5001


⸻

🔐 默认账号

管理员账号
	•	用户名：admin
	•	密码：admin123

⚠️ 部署到生产环境前请务必修改默认密码

⸻

🗄️ 数据库说明
	•	数据库：SQLite
	•	启动时自动创建
	•	默认包含：
	•	10 栋宿舍楼（每栋 10 层）
	•	多种房型（4 人 / 6 人间）
	•	管理员账户
	•	专业基础数据

⸻

🧰 技术栈

层级	技术
后端	Flask · SQLAlchemy · Flask-Login
前端	Bootstrap 5 · Bootstrap Icons
模板	Jinja2
数据库	SQLite
架构	MVC / 模块化设计


⸻

🛠️ 开发建议
	•	使用 models/ 保证数据结构清晰
	•	路由按角色拆分，避免单文件膨胀
	•	复杂逻辑优先放入 service / utils 层
	•	可拓展方向：
	•	Redis 缓存
	•	Celery 异步任务
	•	PostgreSQL / MySQL
	•	Docker 部署

⸻

📜 License

MIT License

⸻

如果这个项目对你有帮助，欢迎 ⭐ Star 或 Fork 进行二次开发
