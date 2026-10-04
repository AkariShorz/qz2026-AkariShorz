# 文章应用的页面地址集中配置在这里
from django.urls import path

from . import views

app_name = "articles"
urlpatterns = [
    path("", views.article_list, name="list"),
    path("accounts/register/", views.register, name="register"),
    path("stats/", views.article_stats, name="stats"),
    path("articles/new/", views.article_create, name="create"),
    path("articles/<int:pk>/", views.article_detail, name="detail"),
    path("articles/<int:pk>/edit/", views.article_edit, name="edit"),
    path("articles/<int:pk>/delete/", views.article_delete, name="delete"),
    path(
        "articles/<int:pk>/attachments/",
        views.attachment_upload,
        name="attachment_upload",
    ),
    path(
        "attachments/<int:pk>/delete/",
        views.attachment_delete,
        name="attachment_delete",
    ),
    path(
        "attachments/<int:pk>/download/",
        views.attachment_download,
        name="attachment_download",
    ),
]
