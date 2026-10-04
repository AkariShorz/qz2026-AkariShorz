# ASGI 是异步服务器启动 Django 项目时使用的入口
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "article_manager.settings")
application = get_asgi_application()
