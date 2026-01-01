# IndieLiteLedger

[English](./README_EN.md) | [简体中文](./README.md)

IndieLiteLedger is a lightweight business assistant designed for independent developers, digital nomads, and startup teams. Built with FastAPI and Vue3, it integrates core features like Customer Relationship Management (CRM), order tracking, financial reconciliation, and sales analysis. It helps you move away from complex spreadsheets and manage your small business in the simplest way possible.

## ⚡ Quick Deploy

To help you get started faster, we have added support for **Docker Offline One-Click Deployment**. No complex environment setup is required—installation can be completed with just a single image file:

- 📦 **Docker Quick Deploy**: Supports one-click startup via `docker-compose` with optimized default configurations.
- 🛠️ **1Panel Integration**: Exclusive orchestration documentation for 1Panel users, providing a "what you see is what you get" experience.

**Deployment Documentation:**
- 📖 [Docker Offline Deployment Guide](./IndieLiteLedger%20Docker%20部署指南.md)
- 🚀 [1Panel Exclusive Deployment Tutorial](./1Panel%20Docker%20部署文档.md)

## 📖 Origin Story

**Evolution from a "Licensing Tool"**

Initially, I just wanted to build a simple licensing tool for an AI RAG system I was developing, to easily manage and generate licenses. However, over time, I realized:

- Licensing alone isn't enough; I need to **manage customers** and track the usage history behind each license.
- Customers alone aren't enough; I need **order management** to clearly know how much revenue I've generated throughout the year.
- Revenue alone isn't enough; I also need **cost tracking** to see how much I'm spending on servers, API interfaces, etc.

Thus, the project gradually evolved from a single tool into its current form: covering the business foundations of **User Management, Sales Management, and Cost Management**. To see at a glance whether I'm making a profit or loss, I further developed **Sales Analysis and a Data Workbench**, making business results visually intuitive through charts.

**To Fellow Travelers**

Having served large enterprises for a long time, I understand the rigor and complexity of big systems. But as an individual or a small team, we don't need to trap ourselves in tedious processes too early, yet we shouldn't live in a muddle day after day. This small software may not make your business boom instantly, but it can help you manage the results of every drop of sweat you put in.

**All data in this software runs locally, so you don't have to worry about privacy leaks. Enjoy!**

![image-20251226214532668](https://typora999.oss-cn-beijing.aliyuncs.com/image-20251226214532668.png)

## 🚀 Features

- **Lightweight & Efficient**: Built on the FastAPI asynchronous framework for excellent performance and simple deployment.
- **Flexible Database**: Supports automatic switching between SQLite (default) and MySQL to meet different stages of needs.
- **Clean Code**: Strict type checking and modular design, making it easy for secondary development.

## 🖼️ Feature Overview

### 👥 Customer Management (CRM)

More than just recording contact info, it's about maintaining business context. Supports customer categorization, source tracking, intention level management, and access record management, fully documenting the growth trajectory of every customer.

![image-20251226215156473](https://typora999.oss-cn-beijing.aliyuncs.com/image-20251226215156473.png)

### 📝 Order Tracking

Full-process automated management. From order creation and payment status changes to renewal reminders, it lets you grasp the flow of every transaction in real-time, moving away from manual ledgers.

![image-20251226215317225](https://typora999.oss-cn-beijing.aliyuncs.com/image-20251226215317225.png)

### 💸 Cost Management

Refined recording of every expenditure. Whether it's server costs, AI API fees, or other operating costs, they can be categorized and recorded, providing accurate data support for profit analysis.

![image-20251226215603627](https://typora999.oss-cn-beijing.aliyuncs.com/image-20251226215603627.png)

### 💰 Workbench

Refined financial dashboard. Combines income and costs to automatically calculate gross profit, customer conversion effectiveness, and cost structure analysis, helping you clearly insight into the business's profitability.

> Same as the homepage, not repeated here!

### 📊 Sales Analysis

Data-driven management. Analyze customer distribution, sales trends, and performance ratios through intuitive dashboards. The workbench lets you see at a glance: how much you earned today and where the future growth lies.

![image-20251226214731334](https://typora999.oss-cn-beijing.aliyuncs.com/image-20251226214731334.png)

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: Vue 3, Vite, TypeScript, UnoCSS, Element Plus
- **Database**: SQLite / MySQL

Note: Why keep SQLite? If an individual doesn't want to set up a separate MySQL service or plans to package it into an EXE for single-machine use, SQLite is more than enough—simple, lightweight, and backup is as easy as copy-paste!

## 🏁 Quick Start

### 1. Environment Preparation

Ensure Python 3.10+ is installed. It's recommended to use a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and modify the configuration as needed (defaults to SQLite).

> Note: If nothing is configured, it defaults to the SQLite database. If MySQL information is configured and uncommented, it will connect to your MySQL database.

### 4. Initialize Database

```bash
python scripts/init_db.py
```

### 5. Start Service

Choose the appropriate startup method according to your operating system:

**Windows (PowerShell):**

```powershell
python -m uvicorn app.main:app --reload
```

**Linux / macOS:**

```bash
uvicorn app.main:app --reload
```

## 📄 License

MIT License
