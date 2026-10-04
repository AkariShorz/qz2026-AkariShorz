from django.apps import AppConfig


class ArticlesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "articles"

    def ready(self):
        # 应用启动时加载信号处理器，否则自动审计和文件处理不会生效
        from . import signals  # noqa: F401
