# 模型信号负责自动记录操作审计，并处理封面缩略图和文件清理
from contextvars import ContextVar
from io import BytesIO

from django.core.files.base import ContentFile
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from PIL import Image, ImageOps

from .models import Article, Attachment, AuditLog

current_actor = ContextVar("current_article_audit_actor", default=None)
# 集中列出要审计的字段，避免前后比较时不小心漏掉重要内容
AUDITED_FIELDS = (
    "title", "content", "status", "author_id", "cover_image", "is_deleted"
)


@receiver(pre_save, sender=Article)
def remember_article_values(sender, instance, **kwargs):
    # 保存前先读取旧值，保存后才能比较字段并记录具体变化
    if instance.pk:
        # 已存在的文章从数据库取旧值；新文章还没有旧记录可比
        instance._audit_old_values = (
            sender.objects.filter(pk=instance.pk)
            .values(*AUDITED_FIELDS)
            .first()
        )
    else:
        instance._audit_old_values = None


@receiver(post_save, sender=Article)
def write_article_audit(sender, instance, created, raw=False, **kwargs):
    # 创建、字段更新和软删除都写入审计记录；字段没变化时就不新增记录
    if raw:
        # raw 通常出现在数据装载过程中，这时跳过业务审计和图片处理
        return
    old_values = getattr(instance, "_audit_old_values", None)
    fields = (
        "title", "content", "status", "author_id", "cover_image", "is_deleted"
    )
    if created or old_values is None:
        # 新建记录的字段统一记成从空值变为当前值
        changes = {}
        for field in fields:
            new_value = getattr(instance, field)
            if field == "cover_image":
                new_value = instance.cover_image.name if instance.cover_image else ""
            changes[field] = {"old": None, "new": new_value}
    else:
        # 更新时只保存实际变化的字段，日志内容会更清楚也更精简
        changes = {}
        for field in fields:
            old_value = old_values[field]
            new_value = getattr(instance, field)
            if field == "cover_image":
                new_value = instance.cover_image.name if instance.cover_image else ""
            if old_value != new_value:
                changes[field] = {"old": old_value, "new": new_value}

    if not changes:
        # 比如只保存了未纳入审计的字段时，不额外写一条空日志
        return

    if created:
        action = AuditLog.Action.CREATE
    elif changes.get("is_deleted", {}).get("new") is True:
        action = AuditLog.Action.DELETE
    elif changes.get("status", {}).get("new") == Article.Status.PUBLISHED:
        action = AuditLog.Action.PUBLISH
    elif changes.get("status", {}).get("new") == Article.Status.ARCHIVED:
        action = AuditLog.Action.ARCHIVE
    else:
        action = AuditLog.Action.UPDATE

    # 操作人由中间件提供；后台脚本等非请求场景下可能没有操作人
    AuditLog.objects.create(
        action=action,
        article=instance,
        actor=current_actor.get(),
        changes=changes,
    )


@receiver(pre_delete, sender=Article)
def audit_hard_article_delete(sender, instance, **kwargs):
    # 永久删除前补一条审计记录，保留文章被删除的信息
    AuditLog.objects.create(
        action=AuditLog.Action.DELETE,
        # Django 的删除收集器此时已经确定待删除对象，新建的日志不会被一起删除；
        # 文章和操作人外键允许为空，因此这里留空以保证日志可以保留下来
        article=None,
        actor=None,
        changes={
            "deleted": {"old": instance.is_deleted, "new": True},
            "title": {"old": instance.title, "new": None},
        },
    )


@receiver(post_save, sender=Article)
def create_cover_thumbnail(sender, instance, created, raw=False, **kwargs):
    # 只有封面变化时才重新生成缩略图，避免无关保存触发重复处理
    if raw:
        return
    # 使用保存前记录的封面名称判断是否换图，不受其他字段更新影响
    old_values = getattr(instance, "_audit_old_values", None)
    old_cover = old_values.get("cover_image") if old_values else None
    new_cover = instance.cover_image.name if instance.cover_image else ""
    if not created and old_cover == new_cover:
        return

    if not new_cover:
        if instance.cover_thumbnail:
            # 封面被清空时，同步移除旧缩略图并保存字段变化
            instance.cover_thumbnail.delete(save=False)
            instance.save(update_fields=["cover_thumbnail"])
        return

    with instance.cover_image.open("rb") as source:
        # 根据图片 EXIF 信息修正方向，再转成 RGB，避免缩略图方向异常
        image = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    target_height = max(1, round(image.height * 200 / image.width))
    # 固定缩略图宽度为 200 像素，高度按原图比例计算
    image = image.resize((200, target_height), Image.Resampling.LANCZOS)
    output = BytesIO()
    image.save(output, format="JPEG", quality=85, optimize=True)

    if instance.cover_thumbnail:
        # 保存新缩略图前先删除旧文件，避免媒体目录里积累无用版本
        instance.cover_thumbnail.delete(save=False)
    instance.cover_thumbnail.save(
        f"article-{instance.pk}.jpg", ContentFile(output.getvalue()), save=False
    )
    instance.save(update_fields=["cover_thumbnail"])


@receiver(post_delete, sender=Attachment)
def remove_attachment_file(sender, instance, **kwargs):
    # 附件记录删除后同步删除磁盘文件，避免留下不再使用的文件
    if instance.file:
        instance.file.storage.delete(instance.file.name)


@receiver(post_delete, sender=Article)
def remove_article_images(sender, instance, **kwargs):
    # 文章永久删除后清理原封面和缩略图文件
    for image_field in (instance.cover_image, instance.cover_thumbnail):
        if image_field:
            image_field.storage.delete(image_field.name)
