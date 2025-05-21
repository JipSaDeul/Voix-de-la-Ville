# 开发环境搭建与启动指南

## 1. 环境准备

建议使用 Anaconda 或 Python 3.10+ 虚拟环境。

### 使用 Anaconda 创建环境
```bash
conda create -n django_env python=3.10
conda activate django_env
```

### 安装依赖
推荐使用 pyproject.toml 进行依赖安装（确保已激活虚拟环境）：
```bash
pip install .[dev]
```
如果你需要 requirements.txt，可以通过如下命令生成：
```bash
pip freeze > requirements.txt
```
（本项目默认未提供 requirements.txt）

## 2. 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

## 3. 创建超级用户（用于后台管理）
```bash
python manage.py createsuperuser
```

## 4. 启动开发服务器
```bash
python manage.py runserver
```

## 5. 访问项目
- 管理后台: http://127.0.0.1:8000/admin/
- 用户认证: http://127.0.0.1:8000/accounts/
- API接口: http://127.0.0.1:8000/api/

## 6. 其他说明
- 图片上传目录为 `media/`，开发环境已自动配置静态与媒体文件服务。
- 如需前端开发或部署，请参考 Workflow.md 的后续阶段说明。
