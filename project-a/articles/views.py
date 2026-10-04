# 页面视图负责查询数据、检查权限并处理用户提交的表单
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ArticleForm, AttachmentForm, RegistrationForm
from .models import Article, Attachment, AuditLog


def register(request):
    # 已登录用户不需要再次注册，直接返回文章列表
    if request.user.is_authenticated:
        return redirect("articles:list")
    if request.method == "POST":
        # POST 请求带着用户刚填的内容，先绑定表单再统一校验
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # UserCreationForm 会验证两次密码是否一致，并使用 Django 的密码哈希
            user = form.save()
            login(request, user)
            messages.success(request, "账号已创建。")
            return redirect("articles:list")
    else:
        form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})


def article_list(request):
    # 过滤软删除文章；访客只能看已发布文章，登录用户也能看自己的文章
    articles = Article.objects.filter(is_deleted=False).select_related("author")
    if request.user.is_authenticated:
        # distinct 用来避免权限筛选组合后出现重复文章
        articles = articles.filter(
            Q(status=Article.Status.PUBLISHED) | Q(author=request.user)
        ).distinct()
    else:
        articles = articles.filter(status=Article.Status.PUBLISHED)
    return render(request, "articles/article_list.html", {"articles": articles})


def article_detail(request, pk):
    # 一次查询同时取出作者，模板检查作者身份时就不用再额外查数据库
    article = get_object_or_404(
        Article.objects.select_related("author"), pk=pk, is_deleted=False
    )
    is_author = request.user.is_authenticated and article.author_id == request.user.pk
    if article.status != Article.Status.PUBLISHED and not is_author:
        # 对无权查看的文章返回 404，避免把草稿是否存在泄露给其他访客
        raise Http404

    # 只查询未删除文章；未发布文章仅允许作者本人查看
    # 使用数据库表达式原子递增浏览量。如果先读出旧值再保存，并发请求可能覆盖彼此的更新，
    # 造成计数丢失。让数据库直接执行加一，结果更可靠
    Article.objects.filter(pk=article.pk, is_deleted=False).update(views=F("views") + 1)
    # update 不会自动改动当前 Python 对象，所以重新读取最新浏览量给模板使用
    article.refresh_from_db(fields=["views"])

    # 审计记录一起取出操作人，详情页可以直接展示谁做了修改
    context = {
        "article": article,
        "attachments": article.attachments.all(),
        "audit_logs": article.audit_logs.select_related("actor").order_by("-timestamp"),
        "is_author": is_author,
        "attachment_form": AttachmentForm(),
    }
    return render(request, "articles/article_detail.html", context)


@login_required
def article_create(request):
    # 只有登录用户可以创建文章；作者由服务器根据当前用户设置，不接受表单指定
    if request.method == "POST":
        # 上传图片属于文件字段，必须同时传 request.FILES
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            messages.success(request, "文章已创建。")
            return redirect("articles:detail", pk=article.pk)
    else:
        form = ArticleForm()
    return render(
        request,
        "articles/article_form.html",
        {"form": form, "heading": "新建文章"},
    )


@login_required
def article_edit(request, pk):
    # 查询时限定文章作者为当前用户，确保用户只能编辑自己的文章
    article = get_object_or_404(Article, pk=pk, is_deleted=False, author=request.user)
    if request.method == "POST":
        # instance 表示更新现有文章，不会误创建一篇新的
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "文章已更新。")
            return redirect("articles:detail", pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(
        request,
        "articles/article_form.html",
        {"form": form, "heading": "编辑文章", "article": article},
    )


@login_required
@require_POST
def article_delete(request, pk):
    # 只接受 POST 请求执行删除，避免普通页面访问意外触发操作
    article = get_object_or_404(Article, pk=pk, is_deleted=False, author=request.user)
    article.delete()
    messages.success(request, "文章已移入回收状态。")
    return redirect("articles:list")


@login_required
@require_POST
def attachment_upload(request, pk):
    # 只有文章作者可以上传附件；表单保存时会清理用户提供的文件名
    article = get_object_or_404(Article, pk=pk, is_deleted=False, author=request.user)
    form = AttachmentForm(request.POST, request.FILES)
    if form.is_valid():
        # 先延迟保存，让附件关联到已经确认权限的文章后再入库
        attachment = form.save(commit=False)
        attachment.article = article
        attachment.save()
        messages.success(request, "附件已上传。")
    else:
        messages.error(request, "请选择有效的附件文件。")
    return redirect("articles:detail", pk=article.pk)


@login_required
@require_POST
def attachment_delete(request, pk):
    attachment = get_object_or_404(
        Attachment.objects.select_related("article"),
        pk=pk,
        article__author=request.user,
        article__is_deleted=False,
    )
    article_pk = attachment.article_id
    attachment.delete()
    messages.success(request, "附件已删除。")
    return redirect("articles:detail", pk=article_pk)


def attachment_download(request, pk):
    attachment = get_object_or_404(
        Attachment.objects.select_related("article", "article__author"),
        pk=pk,
        article__is_deleted=False,
    )
    is_author = (
        request.user.is_authenticated
        and attachment.article.author_id == request.user.pk
    )
    if attachment.article.status != Article.Status.PUBLISHED and not is_author:
        raise Http404
    if not attachment.file:
        # 数据库里可能存在没有文件内容的记录，这种情况不能开始下载
        raise Http404

    attachment_file = attachment.file.open("rb")
    # 在数据库中原子递增下载数，避免并发下载造成计数丢失
    Attachment.objects.filter(pk=attachment.pk).update(downloads=F("downloads") + 1)
    return FileResponse(
        attachment_file, as_attachment=True, filename=attachment.file_name
    )


@login_required
def article_stats(request):
    # 统计排除已删除文章；没有浏览量记录时用 0 显示，避免页面拿到 None
    articles = Article.objects.filter(is_deleted=False)
    status_counts = articles.values("status").annotate(total=Count("id"))
    # 把数据库返回的分组结果整理成模板更容易读取的“状态: 数量”字典
    counts_by_status = {row["status"]: row["total"] for row in status_counts}
    context = {
        "article_count": articles.count(),
        "view_count": articles.aggregate(total=Sum("views"))["total"] or 0,
        "status_counts": counts_by_status,
        "recent_logs": AuditLog.objects.select_related("actor", "article")[:10],
    }
    return render(request, "articles/stats.html", context)
