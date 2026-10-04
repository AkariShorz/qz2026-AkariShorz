# WSGI 是同步服务器启动 Django 项目时使用的入口
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "article_manager.settings")
application = get_wsgi_application()
