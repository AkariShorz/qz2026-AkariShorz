import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from articles.models import Article, Attachment, AuditLog


class ArticleWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.author = user_model.objects.create_user(
            username="author", password="test-password"
        )
        self.other_user = user_model.objects.create_user(
            username="other", password="test-password"
        )
        self.published_article = Article.objects.create(
            title="Published article",
            content="Public content",
            author=self.author,
            status=Article.Status.PUBLISHED,
        )
        self.draft_article = Article.objects.create(
            title="Draft article",
            content="Private content",
            author=self.author,
        )

    def test_anonymous_list_shows_only_published_articles(self):
        response = self.client.get(reverse("articles:list"))

        self.assertContains(response, self.published_article.title)
        self.assertNotContains(response, self.draft_article.title)

    def test_draft_access_is_limited_to_author_and_view_count_increments(self):
        detail_url = reverse(
            "articles:detail", kwargs={"pk": self.draft_article.pk}
        )
        self.assertEqual(self.client.get(detail_url).status_code, 404)

        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(detail_url).status_code, 404)

        self.client.force_login(self.author)
        self.assertEqual(self.client.get(detail_url).status_code, 200)
        self.draft_article.refresh_from_db()
        self.assertEqual(self.draft_article.views, 1)

    def test_only_author_can_edit_and_update_is_audited(self):
        edit_url = reverse(
            "articles:edit", kwargs={"pk": self.published_article.pk}
        )
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.post(edit_url, {}).status_code, 404)

        self.client.force_login(self.author)
        response = self.client.post(
            edit_url,
            {
                "title": "Updated title",
                "content": "Updated content",
                "status": Article.Status.PUBLISHED,
            },
        )

        self.assertRedirects(
            response,
            reverse("articles:detail", kwargs={"pk": self.published_article.pk}),
        )
        self.published_article.refresh_from_db()
        self.assertEqual(self.published_article.title, "Updated title")
        self.assertTrue(
            AuditLog.objects.filter(
                article=self.published_article,
                action=AuditLog.Action.UPDATE,
                actor=self.author,
            ).exists()
        )

    def test_author_delete_is_soft_and_audited(self):
        self.client.force_login(self.author)
        response = self.client.post(
            reverse("articles:delete", kwargs={"pk": self.published_article.pk})
        )

        self.assertRedirects(response, reverse("articles:list"))
        self.published_article.refresh_from_db()
        self.assertTrue(self.published_article.is_deleted)
        self.assertTrue(
            AuditLog.objects.filter(
                article=self.published_article,
                action=AuditLog.Action.DELETE,
                actor=self.author,
            ).exists()
        )

    def test_published_attachment_download_increments_counter(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                attachment = Attachment.objects.create(
                    article=self.published_article,
                    file_name="notes.txt",
                    file=SimpleUploadedFile("notes.txt", b"attachment data"),
                )

                response = self.client.get(
                    reverse(
                        "articles:attachment_download",
                        kwargs={"pk": attachment.pk},
                    )
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b"".join(response.streaming_content), b"attachment data")
                response.close()

                attachment.refresh_from_db()
                self.assertEqual(attachment.downloads, 1)