import io
import shutil
import tempfile
from unittest import mock, skipUnless

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import User
from accounts.roles import AUTHORS, EDITORS, ensure_roles, make_author, make_editor
from core.cache import content_version
from interactions.models import Like, ReadingHistory, TopicFollow

from . import ai_daily, recommender
from .fulltext import build_tsquery
from .models import Article, ArticleDailyView, Category, InterviewQA, MediaFile, NewsSource, Tag
from .rendering import estimate_reading_time, render_markdown
from .textutils import expand_query, normalize


def image_file(name="cover.jpg", size=(2000, 1000)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (30, 90, 200)).save(buffer, "JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


def make_article(category, **kwargs):
    defaults = {
        "title": "مقاله آزمایشی",
        "body": "## مقدمه\n\nمتن\n\n```python\nprint('hi')\n```",
        "status": Article.Status.PUBLISHED,
        "published_at": timezone.now(),
    }
    defaults.update(kwargs)
    return Article.objects.create(category=category, **defaults)


class RenderingTests(TestCase):
    def test_toc_uses_unicode_ids(self):
        html, toc = render_markdown("## مقدمه\n\n### نکات مهم")
        self.assertEqual([t["id"] for t in toc], ["مقدمه", "نکات-مهم"])
        self.assertIn('id="نکات-مهم"', html)

    def test_code_is_highlighted(self):
        html, _ = render_markdown("```python\nimport os\n```")
        self.assertIn('class="highlight"', html)

    def test_script_is_stripped(self):
        html, _ = render_markdown("<script>alert(1)</script> hello")
        self.assertNotIn("<script>", html)

    def test_reading_time(self):
        self.assertEqual(estimate_reading_time(""), 1)
        self.assertEqual(estimate_reading_time("کلمه " * 1000), 5)


class TextUtilsTests(TestCase):
    def test_normalize_arabic_letters_digits_and_zwnj(self):
        self.assertEqual(normalize("كتاب‌هاي ۱۲"), "کتاب های 12")

    def test_expand_query_synonyms_and_phrases(self):
        groups = expand_query("آموزش هوش مصنوعی با پایتون")
        flat = [term for group in groups for term in group]
        self.assertIn("ai", flat)
        self.assertIn("python", flat)
        self.assertIn("tutorial", flat)

    def test_build_tsquery(self):
        self.assertEqual(build_tsquery([["python", "پایتون"], ["deep learning"]]),
                         "('python':* | 'پایتون':*) & ('deep':* <-> 'learning':*)")

    def test_build_tsquery_strips_operators(self):
        query = build_tsquery(expand_query("a' | b & !c:* <-> (d)"))
        self.assertNotIn("!", query)
        self.assertNotIn("(d)", query)
        self.assertEqual(query.count("'"), query.count(":*") * 2)


@skipUnless(connection.vendor == "postgresql", "full-text search runs on PostgreSQL")
class PostgresFullTextTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cat = Category.objects.create(name="برنامه‌نویسی", slug="programming")

    def test_vector_is_indexed_and_ranks_title_first(self):
        body_only = make_article(self.cat, title="Weekly roundup", body="python python python")
        in_title = make_article(self.cat, title="Python packaging", body="wheels")
        results = list(Article.objects.published().search("python").order_by("-rank"))
        self.assertEqual(results, [in_title, body_only])
        with connection.cursor() as cursor:
            cursor.execute("SELECT indexname FROM pg_indexes WHERE tablename = 'magazine_article'")
            self.assertIn("magazine_article_search_vector_gin", {row[0] for row in cursor.fetchall()})

    def test_prefix_persian_and_tag_updates(self):
        article = make_article(self.cat, title="آموزش جنگو", body="ساخت API")
        self.assertIn(article, Article.objects.search("جنگ"))  # prefix
        self.assertIn(article, Article.objects.search("django"))  # synonym
        self.assertNotIn(article, Article.objects.search("kubernetes"))
        article.tags.add(Tag.objects.create(name="Kubernetes"))
        self.assertIn(article, Article.objects.search("kubernetes"))  # tags refresh the vector

    def test_search_view_uses_database_rank(self):
        make_article(self.cat, title="Python tips", body="x")
        response = self.client.get(reverse("magazine:search"), {"q": "python"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)


class RecommenderScaleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cat = Category.objects.create(name="وب", slug="web")

    @override_settings(RECOMMENDER_MAX_DOCS=3)
    def test_index_is_capped_to_newest_articles(self):
        for i in range(5):
            make_article(self.cat, title=f"Article {i}", published_at=timezone.now() - timezone.timedelta(days=i))
        index = recommender.build_index()
        self.assertEqual(len(index.vectors), 3)

    def test_inverted_index_only_scores_overlapping_documents(self):
        a = make_article(self.cat, title="Rust ownership", body="borrow checker lifetimes")
        make_article(self.cat, title="Gardening", body="tomatoes soil water")
        index = recommender.get_index()
        self.assertEqual(set(index.dot_all(index.vectorize("borrow checker"))), {a.pk})

    def test_similar_results_are_cached(self):
        a = make_article(self.cat, title="Rust ownership", body="borrow checker")
        make_article(self.cat, title="Rust lifetimes", body="borrow checker")
        first = recommender.similar_ids(a)
        with mock.patch.object(recommender, "get_index", side_effect=AssertionError("not cached")):
            self.assertEqual(recommender.similar_ids(a), first)


class SmartSearchTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cat = Category.objects.create(name="برنامه‌نویسی", slug="programming")
        self.py = make_article(self.cat, title="Python tips for clean code", body="List comprehensions and more")
        self.js = make_article(self.cat, title="JavaScript closures", body="Scopes explained")

    def test_persian_query_finds_english_article(self):
        self.assertEqual(list(Article.objects.search("پایتون")), [self.py])

    def test_all_terms_must_match(self):
        self.assertEqual(list(Article.objects.search("python closures")), [])

    def test_tags_are_searchable(self):
        self.js.tags.add(Tag.objects.create(name="Frontend"))
        self.assertIn(self.js, Article.objects.search("فرانت اند"))

    def test_relevance_prefers_title_match(self):
        body_only = make_article(self.cat, title="Weekly roundup", body="python python python mention")
        ids = recommender.rank_ids("python", [body_only.pk, self.py.pk])
        self.assertEqual(ids[0], self.py.pk)

    def test_typo_correction_and_suggestions(self):
        self.assertEqual(recommender.correct_query("pyton"), "python")
        response = self.client.get(reverse("magazine:search"), {"q": "pyton"})
        self.assertEqual(response.context["corrected"], "python")
        self.assertIn(self.py, response.context["similar"])

    @skipUnless(connection.vendor == "postgresql", "trigram similarity needs PostgreSQL")
    def test_trigram_typo_tolerance_on_postgres(self):
        from .views import _trigram_suggestions

        self.assertIn(self.js, _trigram_suggestions("javascrpt closure"))

    def test_suggest_endpoint(self):
        response = self.client.get(reverse("magazine:search_suggest"), {"q": "پایتون"})
        self.assertContains(response, self.py.title)


class RecommenderTests(TestCase):
    def setUp(self):
        cache.clear()
        self.ai = Category.objects.create(name="هوش مصنوعی", slug="ai")
        self.web = Category.objects.create(name="وب", slug="web")
        self.llm1 = make_article(self.ai, title="LLM fine-tuning guide", body="transformer attention llm training")
        self.llm2 = make_article(self.ai, title="Serving LLM models", body="llm inference transformer gpu")
        self.css = make_article(self.web, title="CSS grid layouts", body="grid flexbox responsive design")
        self.user = User.objects.create_user("reader", "r@example.com", "pass-12345-x")

    def test_similar_articles_share_topic(self):
        self.assertEqual(self.llm1.related(limit=1), [self.llm2])

    def test_personal_recommendations_follow_reading_history(self):
        ReadingHistory.objects.create(user=self.user, article=self.llm1)
        Like.objects.create(user=self.user, article=self.llm1)
        ids = recommender.for_user_ids(self.user, 2)
        self.assertEqual(ids[0], self.llm2.pk)
        self.assertNotIn(self.llm1.pk, ids)  # already read

    def test_followed_topic_boosts_cold_start(self):
        TopicFollow.objects.create(user=self.user, category=self.web)
        self.assertEqual(recommender.for_user_ids(self.user, 1), [self.css.pk])

    def test_index_invalidated_on_publish(self):
        version = content_version()
        make_article(self.web, title="New")
        self.assertGreater(content_version(), version)


class ArticleModelTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="هوش مصنوعی", slug="ai", icon="🤖")

    def test_unicode_slug_is_unique(self):
        a = make_article(self.cat)
        b = make_article(self.cat)
        self.assertEqual(a.slug, "مقاله-آزمایشی")
        self.assertEqual(b.slug, "مقاله-آزمایشی-2")

    def test_ai_daily_numbering(self):
        first = make_article(self.cat, title="یک", content_type=Article.ContentType.AI_DAILY)
        second = make_article(self.cat, title="دو", content_type=Article.ContentType.AI_DAILY)
        self.assertEqual((first.ai_daily_number, second.ai_daily_number), (1, 2))
        self.assertEqual(second.display_title, "AI Daily #2 — دو")

    def test_published_excludes_drafts_review_and_future(self):
        make_article(self.cat, title="draft", status=Article.Status.DRAFT)
        make_article(self.cat, title="review", status=Article.Status.REVIEW)
        make_article(self.cat, title="future", published_at=timezone.now() + timezone.timedelta(days=1))
        live = make_article(self.cat, title="live")
        self.assertEqual(list(Article.objects.published()), [live])

    def test_youtube_embed(self):
        a = make_article(self.cat, video_url="https://www.youtube.com/watch?v=abc123&t=5")
        self.assertEqual(a.video_embed_url, "https://www.youtube.com/embed/abc123")

    def test_related_prefers_shared_tags(self):
        cache.clear()
        other_cat = Category.objects.create(name="وب", slug="web")
        tag = Tag.objects.create(name="Django")
        a = make_article(self.cat, title="a")
        b = make_article(other_cat, title="b")
        a.tags.add(tag)
        b.tags.add(tag)
        self.assertIn(b, a.related())


class MediaTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.cat = Category.objects.create(name="سخت‌افزار", slug="hardware")

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_cover_variants_are_generated(self):
        article = make_article(self.cat, cover=image_file())
        self.assertEqual(sorted(article.cover_variants, key=int), ["480", "960", "1440"])
        self.assertIn("480w", article.cover_srcset)
        self.assertTrue(article.cover_small.endswith("-480.webp"))

    def test_small_cover_keeps_one_variant(self):
        article = make_article(self.cat, cover=image_file(size=(300, 200)))
        self.assertEqual(list(article.cover_variants), ["300"])

    def test_large_uploads_are_downscaled(self):
        media = MediaFile.objects.create(image=image_file(size=(4000, 2000)))
        self.assertEqual(Image.open(media.image.path).width, 1920)
        self.assertIn("![", media.markdown)

    def test_uploaded_video_and_podcast_feed(self):
        article = make_article(
            self.cat, title="قسمت اول", content_type=Article.ContentType.PODCAST,
            audio_file=SimpleUploadedFile("ep1.mp3", b"ID3fake", content_type="audio/mpeg"),
        )
        self.assertTrue(article.audio_src.endswith(".mp3"))
        response = self.client.get(reverse("podcast_rss"))
        self.assertContains(response, "<enclosure")
        self.assertContains(response, "audio/mpeg")


class ViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cat = Category.objects.create(name="هوش مصنوعی", slug="ai", icon="🤖", show_on_home=True)
        self.article = make_article(self.cat, is_featured=True)
        self.user = User.objects.create_user("ali", "ali@example.com", "pass-12345-x")

    def test_public_pages(self):
        urls = [
            reverse("magazine:home"),
            self.article.get_absolute_url(),
            reverse("magazine:category", args=["ai"]),
            reverse("magazine:content_type", args=["article"]),
            reverse("magazine:ai_daily"),
            reverse("magazine:search") + "?q=آزمایشی",
            reverse("rss"),
            reverse("podcast_rss"),
            reverse("robots"),
            reverse("healthz"),
            "/sitemap.xml",
            "/api/articles/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_draft_hidden_from_public(self):
        draft = make_article(self.cat, title="پیش‌نویس", status=Article.Status.DRAFT)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)

    def test_search_finds_article(self):
        response = self.client.get(reverse("magazine:search"), {"q": "آزمایشی"})
        self.assertContains(response, self.article.title)

    def test_empty_search_shows_no_results_message(self):
        response = self.client.get(reverse("magazine:search"), {"q": "ناموجود"})
        self.assertEqual(response.context["page_obj"].paginator.count, 0)
        self.assertContains(response, "نتیجه‌ای دقیقاً مطابق پیدا نشد")

    def test_detail_counts_view_daily_and_records_history(self):
        self.client.force_login(self.user)
        self.client.get(self.article.get_absolute_url())
        self.client.get(self.article.get_absolute_url())
        self.article.refresh_from_db()
        self.assertEqual(self.article.views_count, 2)
        self.assertEqual(ArticleDailyView.objects.get(article=self.article).views, 2)
        self.assertTrue(ReadingHistory.objects.filter(user=self.user, article=self.article).exists())

    def test_interview_renders_questions(self):
        interview = make_article(self.cat, title="گفت‌وگو", content_type=Article.ContentType.INTERVIEW,
                                 interviewee_name="سارا")
        InterviewQA.objects.create(article=interview, question="سؤال اول؟", answer="پاسخ اول")
        response = self.client.get(interview.get_absolute_url())
        self.assertContains(response, "سؤال اول؟")
        self.assertContains(response, "گفت‌وگو با")

    def test_ai_daily_redirect(self):
        daily = make_article(self.cat, title="روزانه", content_type=Article.ContentType.AI_DAILY)
        response = self.client.get(reverse("magazine:ai_daily_detail", args=[daily.ai_daily_number]))
        self.assertRedirects(response, daily.get_absolute_url(), status_code=301)

    def test_for_you_page(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("magazine:for_you")).status_code, 200)


class FakeParsed:
    def __init__(self, parsed, stop_reason="end_turn"):
        self.parsed_output = parsed
        self.stop_reason = stop_reason


class AIDailyTests(TestCase):
    FEED_ITEMS = [
        {"title": "New open model released", "link": "https://news.example/model", "summary": "A new model."},
        {"title": "GPU prices", "link": "https://news.example/gpu", "summary": "Hardware."},
    ]

    def setUp(self):
        Category.objects.create(name="هوش مصنوعی", slug="ai")
        NewsSource.objects.create(name="Example", feed_url="https://news.example/feed")
        self.draft = ai_daily.AIDailyDraft(
            chosen_item=0, title="مدل متن‌باز جدید", excerpt="خلاصه", body_markdown="## بخش\n\nمتن",
            why_important="مهم است", use_cases="کاربرد", developer_impact="تأثیر", tags=["LLM", "Open Source"],
        )

    def _client(self, response):
        client = mock.Mock()
        client.beta.messages.parse.return_value = response
        return client

    @mock.patch("magazine.ai_daily.fetch_feed")
    def test_generates_issue_for_review(self, fetch_feed):
        fetch_feed.return_value = self.FEED_ITEMS
        client = self._client(FakeParsed(self.draft))
        article = ai_daily.generate_ai_daily(client=client)
        self.assertEqual(article.status, Article.Status.REVIEW)
        self.assertEqual(article.content_type, Article.ContentType.AI_DAILY)
        self.assertEqual(article.source_url, "https://news.example/model")
        self.assertTrue(article.ai_generated)
        self.assertEqual(article.ai_daily_number, 1)
        self.assertEqual(sorted(article.tags.values_list("name", flat=True)), ["LLM", "Open Source"])
        kwargs = client.beta.messages.parse.call_args.kwargs
        self.assertEqual(kwargs["output_format"], ai_daily.AIDailyDraft)
        self.assertIn("New open model released", kwargs["messages"][0]["content"])

    @mock.patch("magazine.ai_daily.fetch_feed")
    def test_used_sources_are_skipped_and_one_issue_per_day(self, fetch_feed):
        fetch_feed.return_value = self.FEED_ITEMS
        ai_daily.generate_ai_daily(client=self._client(FakeParsed(self.draft)))
        self.assertEqual([i["link"] for i in ai_daily.collect_items()], ["https://news.example/gpu"])
        with self.assertRaises(ai_daily.AIDailyError):
            ai_daily.generate_ai_daily(client=self._client(FakeParsed(self.draft)))

    @mock.patch("magazine.ai_daily.fetch_feed")
    def test_refusal_is_reported(self, fetch_feed):
        fetch_feed.return_value = self.FEED_ITEMS
        with self.assertRaises(ai_daily.AIDailyError):
            ai_daily.generate_ai_daily(client=self._client(FakeParsed(None, stop_reason="refusal")))
        self.assertFalse(Article.objects.exists())

    def test_parses_rss_and_atom(self):
        rss = b"""<rss><channel><item><title>A</title><link>https://a</link><description>&lt;b&gt;x&lt;/b&gt;</description></item></channel></rss>"""
        atom = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>B</title><link href="https://b"/><summary>y</summary></entry></feed>"""
        for body, expected in ((rss, ("A", "https://a", "x")), (atom, ("B", "https://b", "y"))):
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = body
            with mock.patch("urllib.request.urlopen", return_value=response):
                item = ai_daily.fetch_feed("https://feed")[0]
            self.assertEqual((item["title"], item["link"], item["summary"]), expected)


class AdminRoleTests(TestCase):
    def setUp(self):
        ensure_roles()
        self.cat = Category.objects.create(name="وب", slug="web")
        self.author = User.objects.create_user("writer", "w@example.com", "pass-12345-x")
        make_author(self.author)
        self.editor = User.objects.create_user("chief", "c@example.com", "pass-12345-x")
        make_editor(self.editor)
        self.other = make_article(self.cat, title="Someone else", status=Article.Status.DRAFT)

    def _post_article(self, status, **files):
        return self.client.post(reverse("admin:magazine_article_add"), {
            "title": "مقاله من", "slug": "", "content_type": "article", "category": self.cat.pk,
            "excerpt": "", "body": "متن", "status": status,
            "published_at_0": "2026-01-01", "published_at_1": "10:00:00",
            "media_files-TOTAL_FORMS": "0", "media_files-INITIAL_FORMS": "0",
            "interview_qas-TOTAL_FORMS": "0", "interview_qas-INITIAL_FORMS": "0",
            **files,
        })

    @override_settings(MAX_VIDEO_UPLOAD_MB=1, MAX_AUDIO_UPLOAD_MB=1)
    def test_upload_size_limits(self):
        self.client.force_login(self.editor)
        big = b"\0" * (1024 * 1024 + 1)
        with override_settings(MEDIA_ROOT=tempfile.mkdtemp()):
            response = self._post_article("draft", video_file=SimpleUploadedFile("v.mp4", big, "video/mp4"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "نباید بیشتر از 1 مگابایت")
            response = self._post_article("draft", audio_file=SimpleUploadedFile("a.mp3", big, "audio/mpeg"))
            self.assertContains(response, "نباید بیشتر از 1 مگابایت")
            self.assertFalse(Article.objects.filter(title="مقاله من").exists())
            small = SimpleUploadedFile("a.mp3", b"ID3" * 10, "audio/mpeg")
            self.assertEqual(self._post_article("draft", audio_file=small).status_code, 302)

    @override_settings(MAX_IMAGE_UPLOAD_MB=0)
    def test_editor_image_upload_limit(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse("magazine:admin_upload"), {"image": image_file("x.jpg", (50, 50))})
        self.assertEqual(response.status_code, 400)

    def test_groups_exist_with_permissions(self):
        self.assertTrue(self.editor.has_perm("magazine.publish_article"))
        self.assertFalse(self.author.has_perm("magazine.publish_article"))
        self.assertTrue(self.author.groups.filter(name=AUTHORS).exists())
        self.assertTrue(self.editor.groups.filter(name=EDITORS).exists())

    def test_author_cannot_publish(self):
        self.client.force_login(self.author)
        response = self._post_article("published")
        self.assertEqual(response.status_code, 200)  # "published" is not an allowed choice
        response = self._post_article("review")
        self.assertEqual(response.status_code, 302)
        article = Article.objects.get(title="مقاله من")
        self.assertEqual((article.status, article.author), (Article.Status.REVIEW, self.author))

    def test_author_sees_only_own_articles(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse("admin:magazine_article_changelist"))
        self.assertNotContains(response, "Someone else")
        response = self.client.get(reverse("admin:magazine_article_change", args=[self.other.pk]))
        self.assertIn(response.status_code, (302, 403))

    def test_editor_can_publish(self):
        self.client.force_login(self.editor)
        response = self._post_article("published")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Article.objects.get(title="مقاله من").status, Article.Status.PUBLISHED)

    def test_dashboard_and_editor_endpoints(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "بازدید روزانه")
        response = self.client.post(reverse("magazine:admin_preview"), {"text": "## سلام\n\n**bold**"})
        self.assertContains(response, "<strong>bold</strong>")
        with override_settings(MEDIA_ROOT=tempfile.mkdtemp()):
            response = self.client.post(reverse("magazine:admin_upload"), {"image": image_file("x.jpg", (100, 100))})
        self.assertEqual(response.status_code, 200)
        self.assertIn("![", response.json()["markdown"])

    def test_editor_endpoints_require_staff(self):
        response = self.client.post(reverse("magazine:admin_preview"), {"text": "x"})
        self.assertEqual(response.status_code, 302)


class ShowcaseTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_replaces_placeholders_and_is_idempotent(self):
        from django.core.management import call_command

        from .management.commands.load_showcase import PHOTO_DIR
        from .showcase import ARTICLES, PHOTOS

        self.assertEqual({a["title"] for a in ARTICLES}, set(PHOTOS))  # every article has a photo
        for photo_id in PHOTOS.values():
            self.assertTrue((PHOTO_DIR / f"{photo_id}.jpg").is_file(), photo_id)

        call_command("seed_magazine", "--demo", stdout=io.StringIO())
        call_command("load_showcase", stdout=io.StringIO())
        call_command("load_showcase", stdout=io.StringIO())

        self.assertEqual(Article.objects.count(), len(ARTICLES))
        self.assertEqual(Article.objects.filter(is_featured=True).count(), 1)
        self.assertFalse(Article.objects.filter(cover="").exists())
        dailies = list(Article.objects.filter(content_type=Article.ContentType.AI_DAILY).order_by("ai_daily_number"))
        self.assertEqual([a.ai_daily_number for a in dailies], list(range(1, len(dailies) + 1)))
        self.assertEqual(dailies, sorted(dailies, key=lambda a: a.published_at))  # newest issue has the top number
        for article in Article.objects.all():
            self.assertEqual(self.client.get(article.get_absolute_url()).status_code, 200, article.title)


class HomeLayoutTests(TestCase):
    def test_home_has_hero_slider_side_stories_and_category_cards(self):
        cats = [Category.objects.create(name=f"دسته {i}", slug=f"c{i}") for i in range(4)]
        top = make_article(cats[0], title="مطلب اصلی", is_featured=True)
        make_article(cats[0], title="منتخب سردبیر", is_editor_pick=True)
        for i, cat in enumerate(cats):
            make_article(cat, title=f"مطلب {i}")
        response = self.client.get(reverse("magazine:home"))
        self.assertContains(response, "data-slider")
        self.assertEqual(response.context["hero_slides"][0], top)
        side_categories = [a.category_id for a in response.context["hero_side"]]
        self.assertEqual(len(side_categories), len(set(side_categories)))  # one per category
        self.assertNotIn(cats[0].pk, side_categories)  # the top story's category is already shown
        self.assertEqual({c.pk for c, _ in response.context["category_cards"]}, {c.pk for c in cats})
