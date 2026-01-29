# 宿舍管理系统 Dorm Management System

> 一个基于 Flask 的宿舍管理系统，围绕“学生选宿、管理员管理、智能匹配与考勤”完整闭环设计，适合作为毕业设计或实际部署使用。


[![GitHub stars](https://img.shields.io/github/stars/13fty/The-simple-flask?style=social)](https://github.com/13fty/The-simple-flask)
[![GitHub forks](https://img.shields.io/github/forks/13fty/The-simple-flask?style=social)](https://github.com/13fty/The-simple-flask)
[![GitHub issues](https://img.shields.io/github/issues/13fty/The-simple-flask)](https://github.com/13fty/The-simple-flask/issues)
[![GitHub license](https://img.shields.io/github/license/13fty/The-simple-flask)](./LICENSE)


---

## 项目简介

本项目实现了一个覆盖**学生端、管理员端与系统管理端**的宿舍管理平台，核心目标是：

- **简化宿舍分配流程**：从选宿申请到管理员审核全流程线上化；
- **提升住宿体验**：通过**室友匹配算法**和宿舍状态展示，让学生更好地选择宿舍与室友；
- **辅助管理决策**：提供宿舍使用情况、考勤数据、公告管理等功能，帮助管理方掌握运行状况。

代码采用 **Flask + Blueprint 模块化** 设计，配合 SQLAlchemy、Flask-Login、Bootstrap 5 等技术，结构清晰，便于二次开发与扩展。

---

## 主要功能概览

### 学生端功能

- **账号注册 / 登录**：基于 `Flask-Login` 的身份认证与会话管理；
- **浏览与筛选宿舍**：按楼栋、人数、性别等条件查看可选宿舍；
- **提交宿舍申请**：支持个人申请与团队（组队）申请；
- **查看申请进度与历史记录**；
- **室友匹配与分配**：
  - 支持根据性别、专业、作息习惯、安静/整洁程度等进行匹配；
  - 自动为学生推荐合适宿舍与床位；
- **团队组建**：发起或加入宿舍团队，一起选择宿舍；
- **消息与公告查看**：查看系统公告、与同学之间的消息（如启用相关模块）。

### 管理员端功能

- **宿舍资源管理**：
  - 宿舍楼、宿舍房间、床位的增删改查；
  - 宿舍容量、性别限制等配置；
- **学生与申请管理**：
  - 审核学生宿舍申请（通过/驳回/变更）；
  - 查看学生当前住宿状态与历史记录；
- **考勤与统计**（如配合考勤功能使用）：
  - 记录与查看出勤/缺勤情况；
  - 统计某栋楼或某间宿舍的考勤数据；
- **公告与系统管理**：
  - 发布、编辑、删除公告；
  - 管理系统全局配置、基础数据等。

### 系统特性

- **模块化架构**：`routes/` + `models/` + `services/` 分层清晰；
- **ORM 持久化**：使用 SQLAlchemy 管理模型与数据库；
- **权限控制**：基于角色（学生 / 管理员）进行访问控制；
- **响应式前端**：使用 Bootstrap 5 和模板继承实现统一 UI；
- **可测试性**：提供 `tests/` 目录与测试脚本，便于自动化回归；
- **可维护性**：`docs/` 中包含改进建议、论文说明等文档。

---

## 系统结构与目录说明

项目主要目录结构（略去缓存与日志等临时文件）：

```text
.
├── start.py                # 主应用入口（Flask app）
├── init_db.py              # 初始化数据库脚本
├── requirements.txt        # Python 依赖
├── README.md               # 项目说明（当前文件）
├── LICENSE                 # MIT 开源许可证
├── .gitignore              # Git 忽略配置
├── .env.example            # 环境变量示例文件
│
├── config/
│   ├── __init__.py
│   ├── config.py           # 通用配置入口（如有）
│   └── settings.py         # 环境与业务配置
│
├── models/                 # 数据模型层
│   ├── __init__.py
│   ├── database.py         # 数据库实例与枚举（UserRole、BedStatus 等）
│   ├── user.py             # 用户与学生相关模型
│   ├── dormitory.py        # 宿舍楼、宿舍、床位模型
│   ├── application.py      # 宿舍申请、团队等模型
│   ├── system.py           # 公告、系统配置、审计等模型
│   └── audit.py            # 审计日志模型（如启用）
│
├── routes/                 # 路由与控制器层（Blueprint）
│   ├── __init__.py
│   ├── main.py             # 首页与通用路由
│   ├── auth.py             # 登录注册、认证相关路由
│   ├── student.py          # 学生端业务路由（如有）
│   ├── dorm.py             # 宿舍浏览、申请相关路由
│   ├── admin.py            # 管理员端业务路由
│   └── attendance.py       # 考勤相关路由（按需使用）
│
├── services/               # 业务服务层
│   ├── dorm_service.py     # 宿舍业务逻辑封装
│   └── user_service.py     # 用户相关业务逻辑封装
│
├── templates/              # Jinja2 模板
│   ├── base.html           # 基础布局
│   ├── index.html          # 首页
│   ├── auth/               # 登录注册等模板
│   ├── student/            # 学生端页面
│   ├── admin/              # 管理员后台页面
│   ├── dorms/              # 宿舍浏览、详情、变更等页面
│   ├── messages/           # 消息相关页面（如启用）
│   ├── reviews/            # 评价相关页面（如启用）
│   ├── roommate/           # 室友匹配相关页面
│   └── errors/             # 404 / 500 等错误页
│
├── static/                 # 静态资源
│   ├── css/
│   │   └── style.css       # 自定义样式
│   └── js/
│       └── main.js         # 前端交互脚本
│
├── scripts/                # 辅助脚本
│   ├── add_dormitories.py  # 批量添加宿舍与床位数据
│   ├── migrate_add_fields.py
│   ├── migrate_attendance.py
│   ├── test_dorm_change_with_validation.py
│   └── test_system.py      # 端到端测试或检查脚本
│
├── docs/                   # 项目文档
│   ├── README.md           # 文档目录说明
│   ├── ATTENDANCE_FEATURE.md  # 考勤功能设计文档
│   ├── IMPROVEMENTS.md     # 改进建议与已知问题
│   └── paper.md            # 论文相关内容
│
├── tests/
│   └── test_dorm_system.py # pytest 测试用例
│
└── archive/                # 历史版本与归档代码（不再使用）
    ├── app.py
    ├── audit.py
    ├── create_db.py
    ├── maintenance.py
    ├── notification.py
    ├── run.py
    └── visitor.py
```

---

## 技术栈与架构设计

- **后端框架**：Flask（Blueprint 模块化、工厂模式友好）
- **ORM 与数据库**：Flask‑SQLAlchemy + SQLite
- **认证与会话**：Flask‑Login
- **安全与密码**：Werkzeug（密码哈希）
- **前端**：Bootstrap 5、Bootstrap Icons、Jinja2 模板
- **日志与监控**：`logs/` 目录记录运行日志（`.gitignore` 中已忽略）
- **部署目标**：优先本地开发 / 校园内网部署，可扩展到 WSGI（如 Gunicorn + Nginx）

逻辑上主要分为三层：

1. **路由层 (`routes/`)**：接收 HTTP 请求，做参数校验与权限检查；
2. **服务层 (`services/`)**：封装宿舍分配、用户操作等复杂业务逻辑；
3. **数据层 (`models/`)**：定义数据模型、枚举类型和数据库会话。

---

## 快速开始

### 1. 环境要求

详见 `setting.md` 与 `docs/ATTENDANCE_FEATURE.md`，核心要求：

- Python 3.9+
- 已安装 SQLite3（macOS / 大部分 Linux 自带）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

建议使用虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate      # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 初始化数据库（首次运行）

```bash
python init_db.py
```

这一步会自动创建：

- 宿舍楼、宿舍、床位基础数据；
- 管理员默认账号；
- 部分专业等基础业务数据。

### 4. （可选）添加或迁移宿舍数据

```bash
python scripts/add_dormitories.py
python scripts/migrate_add_fields.py
python scripts/migrate_attendance.py   # 如需考勤数据结构
```

### 5. 运行应用

```bash
python start.py
```

启动后在浏览器访问：

```text
http://localhost:5001
```

---

## 默认账号与角色

### 管理员账号

- 用户名：`admin`
- 密码：`admin123`

建议在首次登录后立即修改密码，并根据实际使用场景创建更多管理员或学生账号。

---

## 核心业务流程简介

### 1. 学生选宿流程

1. 学生注册并登录系统；
2. 浏览宿舍楼 / 宿舍信息，查看剩余床位与宿舍详情；
3. 提交宿舍申请（单人或组队）；
4. 等待管理员审核结果（通过 / 驳回 / 调整）；
5. 审核通过后，系统为学生绑定对应床位，更新宿舍入住状态。

### 2. 室友匹配与宿舍分配

系统在 `start.py` 与 `models/` / `services/` 中实现了一套**基于规则与打分的床位分配逻辑**，大致考虑：

- 性别匹配（楼栋性别限制）；
- 宿舍人数偏好（4 人间 / 6 人间等，含一定的“向下兼容”策略）；
- 专业相近程度；
- 作息时间、安静程度、整洁程度等生活习惯；

通过对可用床位打分，选择得分最高的床位分配给学生，从而提升宿舍内部的匹配度与和谐程度。

### 3. 管理员审核与日常管理

- 在管理员后台可以：
  - 查看所有待审核申请；
  - 对申请进行审批，附带备注；
  - 管理宿舍资源（新增、修改、下线宿舍与床位）；
  - 发布公告、查看统计数据与日志信息。

---

## 开发 & 测试

### 本地开发建议

- 使用虚拟环境隔离依赖；
- 将真实配置放在 `.env`（基于 `.env.example`）中，避免直接写死在代码里；
- 根据需要调整 `config/settings.py` 与 `models/database.py` 中的配置（如数据库路径）。

### 运行测试

本项目提供基础测试用例与测试脚本，推荐使用 `pytest`：

```bash
pip install pytest
pytest
```

如需更复杂的集成测试，可参考 `scripts/test_system.py` 与 `tests/test_dorm_system.py` 自行扩展。

---

## Roadmap / 后续计划（示例）

- [ ] 更完善的考勤统计与可视化界面；
- [ ] 引入角色/权限管理面板（基于 RBAC）；
- [ ] 支持多数据库（如 MySQL / PostgreSQL）；
- [ ] 接入消息通知（邮件 / 企业微信 / 钉钉等）；
- [ ] Docker 化部署与 CI/CD 流程。

你可以根据自己实际开发进度打勾或增删条目。

---

## 开源许可证

本项目基于 **MIT License** 开源，详情见 `LICENSE` 文件。


