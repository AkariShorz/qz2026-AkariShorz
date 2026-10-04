# 在这里配置管理后台中的数据展示方式和操作权限
from django.contrib import admin

from .models import Article, Attachment, AuditLog


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "views", "is_deleted", "created_at")
    list_filter = ("status", "is_deleted", "created_at")
    search_fields = ("title", "content", "author__username")
    readonly_fields = ("views", "created_at", "updated_at", "cover_thumbnail")

    def delete_queryset(self, request, queryset):
        for article in queryset.iterator():
            article.delete()


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("file_name", "article", "downloads", "uploaded_at")
    search_fields = ("file_name", "article__title")
    readonly_fields = ("downloads", "uploaded_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "article", "actor", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("article__title", "actor__username")
    readonly_fields = ("action", "article", "actor", "timestamp", "changes")

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        # 工作人员可以查看审计记录，但不能修改历史记录，避免审计结果失真
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
