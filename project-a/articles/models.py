# 这里定义文章、附件和审计记录对应的数据库模型
from pathlib import Path

from django.conf import settings
from django.db import models


def attachment_upload_path(instance, filename):
    # 去掉用户文件名中可能包含的路径，只保留文件名并按文章分目录保存
    safe_name = Path(filename.replace("\\", "/")).name
    return f"attachments/{instance.article_id}/{safe_name}"


class Article(models.Model):
    class Status(models.TextChoices):
        # 使用 TextChoices 同时约束数据库值并提供页面显示名称
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"
        ARCHIVED = "archived", "已归档"

    title = models.CharField("标题", max_length=200)
    content = models.TextField("正文")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name="作者",
    )
    status = models.CharField(
        "状态", max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    views = models.PositiveBigIntegerField("浏览量", default=0)
    cover_image = models.ImageField("封面图", upload_to="covers/", blank=True)
    cover_thumbnail = models.ImageField(
        "封面缩略图", upload_to="thumbnails/", blank=True, editable=False
    )
    is_deleted = models.BooleanField("已删除", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        # 默认让新文章排在前面，并为常用筛选条件建立索引
        verbose_name = "文章"
        verbose_name_plural = "文章"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "is_deleted"], name="article_status_active_idx"
            ),
            models.Index(
                fields=["author", "created_at"],
                name="article_author_created_idx",
            ),
        ]

    def __str__(self):
        return self.title

    def delete(self, using=None, keep_parents=False):
        # 普通删除采用软删除：标记文章已删除，保留文章数据和审计记录
        if self.is_deleted:
            return 0, {}
        self.is_deleted = True
        self.save(using=using, update_fields=["is_deleted", "updated_at"])
        return 1, {self._meta.label: 1}

    def hard_delete(self, using=None, keep_parents=False):
        # 需要永久删除时调用父类方法；相关删除信号会负责清理和记录
        return super().delete(using=using, keep_parents=keep_parents)


class Attachment(models.Model):
    # 文件名单独保存，下载时可用原始名称返回给浏览器
    file_name = models.CharField("文件名", max_length=255)
    file = models.FileField("文件", upload_to=attachment_upload_path)
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="所属文章",
    )
    downloads = models.PositiveBigIntegerField("下载次数", default=0)
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "附件"
        verbose_name_plural = "附件"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.file_name


class AuditLog(models.Model):
    class Action(models.TextChoices):
        # 操作类型存稳定的英文值，管理页面展示对应中文名称
        CREATE = "create", "创建"
        UPDATE = "update", "更新"
        PUBLISH = "publish", "发布"
        ARCHIVE = "archive", "归档"
        DELETE = "delete", "删除"

    action = models.CharField("操作类型", max_length=10, choices=Action.choices)
    article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="文章",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="article_audit_logs",
        verbose_name="操作人",
    )
    timestamp = models.DateTimeField("操作时间", auto_now_add=True)
    changes = models.JSONField("变更摘要", default=dict)

    class Meta:
        verbose_name = "操作审计日志"
        verbose_name_plural = "操作审计日志"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_action_display()} · {self.timestamp:%Y-%m-%d %H:%M:%S}"
