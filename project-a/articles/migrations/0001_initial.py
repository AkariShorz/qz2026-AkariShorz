# 初始数据库结构：执行首次迁移时，Django 会根据这里的定义创建数据表
import articles.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Article",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="标题")),
                ("content", models.TextField(verbose_name="正文")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "草稿"),
                            ("published", "已发布"),
                            ("archived", "已归档"),
                        ],
                        default="draft",
                        max_length=10,
                        verbose_name="状态",
                    ),
                ),
                (
                    "views",
                    models.PositiveBigIntegerField(default=0, verbose_name="浏览量"),
                ),
                (
                    "cover_image",
                    models.ImageField(
                        blank=True, upload_to="covers/", verbose_name="封面图"
                    ),
                ),
                (
                    "cover_thumbnail",
                    models.ImageField(
                        blank=True,
                        editable=False,
                        upload_to="thumbnails/",
                        verbose_name="封面缩略图",
                    ),
                ),
                ("is_deleted", models.BooleanField(default=False, verbose_name="已删除")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="articles",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="作者",
                    ),
                ),
            ],
            options={
                "verbose_name": "文章",
                "verbose_name_plural": "文章",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["status", "is_deleted"],
                        name="article_status_active_idx",
                    ),
                    models.Index(
                        fields=["author", "created_at"],
                        name="article_author_created_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Attachment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file_name", models.CharField(max_length=255, verbose_name="文件名")),
                (
                    "file",
                    models.FileField(
                        upload_to=articles.models.attachment_upload_path,
                        verbose_name="文件",
                    ),
                ),
                (
                    "downloads",
                    models.PositiveBigIntegerField(default=0, verbose_name="下载次数"),
                ),
                (
                    "uploaded_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="上传时间"),
                ),
                (
                    "article",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="articles.article",
                        verbose_name="所属文章",
                    ),
                ),
            ],
            options={
                "verbose_name": "附件",
                "verbose_name_plural": "附件",
                "ordering": ["-uploaded_at"],
            },
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("create", "创建"),
                            ("update", "更新"),
                            ("publish", "发布"),
                            ("archive", "归档"),
                            ("delete", "删除"),
                        ],
                        max_length=10,
                        verbose_name="操作类型",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(auto_now_add=True, verbose_name="操作时间"),
                ),
                ("changes", models.JSONField(default=dict, verbose_name="变更摘要")),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="article_audit_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="操作人",
                    ),
                ),
                (
                    "article",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to="articles.article",
                        verbose_name="文章",
                    ),
                ),
            ],
            options={
                "verbose_name": "操作审计日志",
                "verbose_name_plural": "操作审计日志",
                "ordering": ["-timestamp"],
            },
        ),
    ]
