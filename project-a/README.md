# 叠甲叠甲Sorrrry
- 肥肠抱歉...... 
- 这个项目工程量有点小大
- 每一个模块我先在本地处理好了再上传

# AI 工具使用说明
- 本项目开发过程中使用 Codex 辅助完成
- 本人与AI的分工如下：
- 本人：提供了项目开发思路，模块分布+构建，项目各模块上传，项目本地运行测试
- AI：代码编辑，代码拆解分析，完善内容，检查项目稳定，以及是否合规
- 项目开发过程中的确有部分我尚未掌握的知识点，后续我将继续努力学习！！！ o,=2 #<<这是一个颜文字嘻嘻

# 项目本身-文章管理系统
 ## 功能
 - 文章状态管理：草稿、已发布、已归档；每个作者只能编辑自己的文章
 - 文件+附件上传、下载计数和作者删除；开发环境通过 `/media/` 访问上传文件
 - Django 信号自动记录文章创建、更新、发布、归档和删除；详情页展示文章审计记录
 - 文章详情访问量和附件下载量使用数据库原子表达式递增
 - 封面图自动生成宽 200px 的缩略图
 - `/stats/` 展示文章统计及最近审计记录；文章删除为软删除
 - Django 内置认证与密码哈希；注册表单调用 `set_password`，并且管理员也可管理用户

 ## 核心逻辑
 - 创建或编辑文章时，`Article` 的保存信号会对比保存前后的字段，并把差异写入 `AuditLog`。请求中间件通过上下文变量提供当前操作人，因此审计记录能标明是谁完成了操作
 - 删除文章会把 `is_deleted` 设为 `True`，列表和详情查询都会过滤这类文章；文章数据和审计历史仍保留。需要永久清理时，模型提供单独的 `hard_delete()` 方法
 - 详情页的浏览量和附件下载量都用数据库表达式 `F(字段) + 1` 更新。这样加一操作由数据库执行，多个请求同时到达时不会因为先读出旧值再保存而覆盖彼此的计数
 - 封面变化后，信号使用 Pillow 读取图片方向并生成 200px 宽的 JPEG 缩略图；文章或附件被永久删除时会清理对应的媒体文件
 - 普通用户只能编辑自己的文章和附件；未登录用户只能查看已发布文章。操作审计在后台只读，避免管理页面直接改写历史记录

 ## 主要目录

```text
article_manager/  Django 设置与 URL 配置
articles/         数据模型、表单、视图、信号和页面模板
templates/        登录页面
media/            本地上传文件（运行时生成，不提交到仓库）
```

 ## 依赖安装

 - 需要 Python 3.10 或更新版本!!!
 - 安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 检查与测试

在本目录执行 Django 配置、迁移和文章应用测试：

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test articles
```

 ## 运行

在本目录(project-a)执行：

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

打开 http://127.0.0.1:8000/ 或 http://localhost:8000/ 浏览文章，访问 `/admin/` 管理用户和数据。`MEDIA_ROOT` 默认为本目录下的 `media/`，仅在 `DEBUG=True` 时由 Django 开发服务器提供媒体文件

文章和附件管理要求登录。可在首页注册账号，Django 的 `UserCreationForm` 会通过 `set_password` 哈希密码后保存；也可由超级用户在管理后台创建和管理用户
