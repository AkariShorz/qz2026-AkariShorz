# 表单负责校验用户输入，确认格式合适后再交给视图和模型处理
from pathlib import Path

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Attachment


class ArticleForm(forms.ModelForm):
    class Meta:
        # 作者、浏览量和删除状态由服务器管理，不开放给普通表单提交
        model = Article
        fields = ("title", "content", "status", "cover_image")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 12}),
        }


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ("file",)

    def save(self, commit=True):
        # 先让 ModelForm 生成对象但暂不入库，方便补充清理后的文件名
        attachment = super().save(commit=False)
        uploaded_file = self.cleaned_data["file"]
        attachment.file_name = Path(
            uploaded_file.name.replace("\\", "/")
        ).name
        if commit:
            # commit=False 时由视图补上所属文章后再自行保存
            attachment.save()
        return attachment


class RegistrationForm(UserCreationForm):
    # 复用 Django 的注册表单；它会哈希密码后再保存，不会存明文密码

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")
