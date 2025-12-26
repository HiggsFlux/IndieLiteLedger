# IndieLiteLedger

IndieLiteLedger 是一款专为独立开发者、数字游民和初创团队打造的轻量级业务助手。基于 FastAPI + Vue3 开发，集成了客户管理 (CRM)、订单追踪、财务对账及销售分析等核心功能，助你告别繁琐表格，用最简单的方式管理自己的小生意。

(A lightweight business assistant for indie developers and small teams to manage CRM, orders, and finances. Built with FastAPI & Vue3, featuring high performance, clean code, and auto-switching between SQLite/MySQL.)

## 🚀 特性

- **轻量高效**：基于 FastAPI 异步框架，性能卓越，部署简单。
- **数据库灵活**：支持 SQLite（默认）和 MySQL 自动切换，满足不同阶段需求。
- **核心业务全覆盖**：
  - 👥 **客户管理 (CRM)**：轻松维护客户关系与联系人。
  - 📝 **订单追踪**：全流程管理业务订单，状态实时掌握。
  - 💰 **财务统计**：收支一目了然，支持成本管理与利润分析。
  - 📊 **销售分析**：直观的仪表盘展示，数据驱动决策。
- **代码整洁**：严格的类型检查与模块化设计，易于二次开发。

## 🛠️ 技术栈

- **后端**: Python 3.10+, FastAPI, SQLAlchemy, Pydantic
- **前端**: Vue 3, Vite, TypeScript, UnoCSS, Element Plus
- **数据库**: SQLite / MySQL

## 🏁 快速开始

### 1. 环境准备
确保已安装 Python 3.10+。建议使用虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置文件
复制 `.env.example` 为 `.env`，并根据需要修改配置（默认使用 SQLite）。

### 4. 初始化数据库
```bash
python scripts/init_sys_config.py
```

### 5. 启动服务
```bash
uvicorn app.main:app --reload
```

访问 `http://127.0.0.1:8000/docs` 查看 API 文档。

## 📄 开源协议

MIT License
