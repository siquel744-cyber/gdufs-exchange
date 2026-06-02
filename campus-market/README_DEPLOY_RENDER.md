部署到 Render（Flask + Gunicorn）完整指南

概览
- 该仓库包含一个 Flask 应用（`app.py`）、静态资源位于 `static/`、上传图片保存在 `uploads/`（当前为本地 SQLite）。
- 我们已添加 `Procfile` 和 `requirements.txt`（包含 `gunicorn`），可直接部署到 Render 的 Web Service。

准备工作（本地）
1. 确保代码已提交到 GitHub 仓库。
2. 在本地运行并测试：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
打开 http://127.0.0.1:5000/ 验证页面和上传功能（注意：本地使用 SQLite，Render 上临时文件系统会丢失，见下文）。

重要文件
- `requirements.txt`：依赖包（包含 `gunicorn`）。
- `Procfile`：`web: gunicorn --bind $PORT app:app`，Render 会读取以启动 Gunicorn。
- `app.py`：Flask 应用入口（已配置 `static` 目录）。

环境变量（在 Render 服务设置）
- `SECRET_KEY`：Flask 会话密钥。务必设置为强随机字符串。
- `DATABASE_URL`（可选）：如果使用外部数据库（推荐使用 Render PostgreSQL），填入数据库连接 URL（例如 `postgres://...`）。当前代码默认使用本地 SQLite 文件 `campus_market.db`，但 SQLite 在 Render 部署时可能不会保持持久性。
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `S3_BUCKET`（可选）：若将上传持久化到 S3，请配置并修改 `app.py` 使用 S3。

建议（生产准备）
- 持久化数据：在 Render 上推荐使用 Render Managed Postgres（或其他外部数据库）替代 SQLite。然后修改代码使用 Postgres（可用 SQLAlchemy 简化迁移）。
- 上传文件持久化：Render 的实例磁盘可能随部署替换而清空，建议将上传保存到 S3 或其他对象存储，并在 `app.py` 使用 boto3 上传/读取。

在 Render 创建服务（图形化步骤）
1. 登录 Render 控制台（https://render.com）。
2. 点击 “New” -> “Web Service”。
3. 选择连接到你的 GitHub 帐号并选择仓库（或使用手动连接）。
4. Branch 选择 `main`（或你想要部署的分支）。
5. Build Command：留空 或 `pip install -r requirements.txt`（Render 会自动运行 pip 安装）。
6. Start Command：留空（Render 会使用 `Procfile` 中的命令 `web: gunicorn --bind $PORT app:app`）。
7. Environment：在此页面添加上面提到的环境变量，例如 `SECRET_KEY`、`DATABASE_URL`（如果使用）。
8. 点击 Create Web Service，Render 会开始构建并启动应用。

配置域名（可选）
1. 在服务页面点击 “Settings” -> “Custom Domains”。
2. 添加你的域名（例如 `market.example.com`）。
3. 按照 Render 提供的 DNS 记录将你的域名指向 Render 的 CNAME/A 记录。
4. 等待 DNS 生效（可能需要几分钟到数小时），Render 会自动为你启用 Let’s Encrypt TLS 证书。

运行前检查清单
- 已将 `gunicorn` 添加到 `requirements.txt`。
- 已添加 `Procfile`（`web: gunicorn --bind $PORT app:app`）。
- `app.py` 已设置 `static_folder='static'` 并保留上传目录 `uploads/`。
- 如果你要保持上传持久性，请准备外部对象存储（S3 等）或使用 Render disk（注意 Render 的免费计划可能有限制）。

本地到 GitHub 到 Render 的快速命令示例
```bash
# 初始化 git（若尚未）
git init
git add .
git commit -m "Initial commit"
# 创建远程并推送（假设已在 GitHub 创建仓库）
git remote add origin git@github.com:youruser/yourrepo.git
git branch -M main
git push -u origin main
```
然后在 Render UI 创建服务并连接该仓库。

若需我帮你：
- 将上传改为使用 S3 并更新 `app.py`（包括上传/读取逻辑）；
- 或将数据库迁移到 PostgreSQL（包括 SQLAlchemy 改造）；
- 或我可以为你生成一份带图的操作手册（每步截图/说明）。

安全提示
- 切勿将 `SECRET_KEY`、数据库密码或 S3 密钥上传到公开仓库。
- 在生产环境使用 HTTPS（Render 会自动配置 TLS）。

常见问题
- Q: 为什么我的上传在重启后丢失？
  A: Render 的实例磁盘并非持久存储；使用外部对象存储或 Render Managed Volumes 来保留文件。

---
如需我现在继续（例如把上传改为 S3 或将 DB 改为 Postgres 并帮你迁移），告诉我你更倾向哪种方案。