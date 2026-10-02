"""Create the magazine's base categories and pages; optionally demo content.

    python manage.py seed_magazine          # categories + static pages
    python manage.py seed_magazine --demo   # ... plus a demo author and sample articles
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Page
from accounts.roles import ensure_roles
from magazine.models import Article, Category, InterviewQA, NewsSource, Tag

# (slug, icon, name, description, show_on_home)
CATEGORIES = [
    ("ai", "🤖", "هوش مصنوعی و یادگیری ماشین", "مدل‌های زبانی، یادگیری عمیق، بینایی ماشین و ابزارهای AI", True),
    ("programming", "💻", "برنامه‌نویسی", "زبان‌ها، الگوها، معماری نرم‌افزار و تجربه‌های کدنویسی", True),
    ("web", "🌐", "توسعه وب", "فرانت‌اند، بک‌اند، فریم‌ورک‌ها و استانداردهای وب", False),
    ("security", "🔐", "امنیت سایبری", "آسیب‌پذیری‌ها، حملات، دفاع و حریم خصوصی", True),
    ("cloud-devops", "☁️", "Cloud و DevOps", "کانتینرها، Kubernetes، CI/CD و زیرساخت ابری", False),
    ("database", "🗄️", "دیتابیس", "SQL، NoSQL، طراحی داده و بهینه‌سازی کوئری", False),
    ("computer-science", "🧠", "علوم کامپیوتر", "الگوریتم‌ها، ساختمان داده و مبانی نظری", False),
    ("hardware", "🖥️", "سخت‌افزار", "پردازنده، GPU، تراشه‌ها و قطعات", False),
    ("gaming", "🎮", "گیم و تکنولوژی", "موتورهای بازی، کنسول‌ها و صنعت گیم", False),
    ("mobile", "📱", "موبایل و فناوری", "اندروید، iOS، اپلیکیشن‌ها و گجت‌ها", False),
    ("news-trends", "🚀", "اخبار و ترندهای IT", "تازه‌ترین رویدادها و روندهای دنیای فناوری", False),
    ("tutorials", "📚", "آموزش و Tutorials", "آموزش‌های گام‌به‌گام و کاربردی", False),
    ("research", "🔬", "مقالات علمی و Research", "مرور و تحلیل پژوهش‌های علمی روز", False),
]

PAGES = [
    ("about", "درباره ما", "**مجله فناوری** رسانه‌ای فارسی برای علاقه‌مندان و متخصصان دنیای IT است.\n\n"
                          "ما هر روز مقاله، خبر، آموزش و تحلیل تازه از دنیای هوش مصنوعی، برنامه‌نویسی، "
                          "امنیت و فناوری منتشر می‌کنیم."),
    ("contact", "تماس با ما", "برای همکاری، پیشنهاد یا ارسال مطلب با ما در ارتباط باشید."),
    ("privacy", "حریم خصوصی", """## چه اطلاعاتی جمع‌آوری می‌کنیم؟

**اگر حساب کاربری بسازید:**

- نام کاربری، آدرس ایمیل و رمز عبور (رمز عبور به‌صورت رمزنگاری‌شده و غیرقابل‌بازگشت ذخیره می‌شود)
- اطلاعاتی که خودتان در پروفایل وارد می‌کنید: نام، بیوگرافی، عکس، وب‌سایت و نام کاربری گیت‌هاب
- فعالیت شما در سایت: مطالب ذخیره‌شده، لایک‌ها، دیدگاه‌ها، موضوع‌های دنبال‌شده و تاریخچهٔ مطالعه

**اگر عضو خبرنامه شوید:** فقط آدرس ایمیل شما.

**هنگام بازدید از سایت:** سرور مانند همهٔ وب‌سایت‌ها آدرس IP، نوع مرورگر و صفحه‌های بازدیدشده را در
گزارش‌های فنی (لاگ) ثبت می‌کند.

## از این اطلاعات چه استفاده‌ای می‌کنیم؟

- ارائهٔ امکانات حساب کاربری مثل ذخیرهٔ مطالب، دیدگاه و تاریخچهٔ مطالعه
- پیشنهاد مطالب مرتبط بر اساس موضوع‌های مورد علاقهٔ شما
- ارسال ایمیل‌های ضروری (تأیید ایمیل، بازیابی رمز عبور، هشدارهای امنیتی)
- ارسال خبرنامه و اعلان مطالب جدید، فقط اگر خودتان آن را فعال کرده باشید
- حفظ امنیت سایت و جلوگیری از سوءاستفاده

**ما اطلاعات شما را نمی‌فروشیم و برای تبلیغات در اختیار دیگران قرار نمی‌دهیم.**

## کوکی‌ها

سایت فقط از کوکی‌های ضروری استفاده می‌کند: کوکی نشست برای ورود به حساب و کوکی امنیتی (CSRF) برای
محافظت از فرم‌ها. انتخاب تم روشن یا تیره هم فقط در مرورگر خود شما ذخیره می‌شود.

## سرویس‌هایی که با آن‌ها کار می‌کنیم

- **میزبانی سایت:** اطلاعات سایت روی سرورهای شرکت میزبان نگهداری می‌شود.
- **ارسال ایمیل:** ایمیل‌های سایت از طریق سرویس ایمیل ارسال می‌شوند.
- **ورود با گوگل یا گیت‌هاب:** اگر این روش را انتخاب کنید، آن سرویس نام و ایمیل شما را در اختیار ما قرار می‌دهد.

## حقوق شما

- اطلاعات پروفایل را هر زمان از صفحهٔ «ویرایش پروفایل» تغییر دهید.
- اشتراک خبرنامه را با لینک انتهای هر ایمیل لغو کنید.
- اعلان‌های ایمیلی را از همان صفحهٔ «ویرایش پروفایل» خاموش کنید.
- برای دریافت یا حذف کامل اطلاعات حسابتان از صفحهٔ «تماس با ما» درخواست بدهید.

## تغییرات این صفحه

اگر این سیاست تغییر کند، نسخهٔ جدید در همین صفحه منتشر می‌شود."""),
    ("terms", "قوانین استفاده", """با استفاده از این سایت و ساخت حساب کاربری، قوانین زیر را می‌پذیرید.

## حساب کاربری

- مسئولیت حفظ رمز عبور و فعالیت‌هایی که با حساب شما انجام می‌شود با خود شماست.
- اطلاعاتی که هنگام ثبت‌نام وارد می‌کنید باید درست باشد.
- هر فرد فقط برای استفادهٔ شخصی حساب می‌سازد؛ ساخت حساب‌های متعدد برای دور زدن محدودیت‌ها مجاز نیست.

## دیدگاه‌ها و محتوای کاربران

ارسال این موارد ممنوع است:

- توهین، تهدید یا آزار دیگران
- تبلیغات ناخواسته (اسپم) و لینک‌های فریبنده
- محتوای غیرقانونی یا ناقض حق نشر دیگران
- اطلاعات شخصی دیگران بدون اجازهٔ آن‌ها

مسئولیت دیدگاه‌ها با نویسندهٔ آن‌هاست. ما می‌توانیم دیدگاه‌هایی را که با این قوانین مغایرند بدون اطلاع
قبلی حذف کنیم و در صورت تکرار، حساب کاربر را مسدود کنیم.

## مالکیت محتوا

- حق نشر مقاله‌ها، آموزش‌ها و تصاویر سایت متعلق به مجله یا صاحبان آن‌هاست.
- نقل بخش‌هایی از مطالب با ذکر منبع و لینک به مطلب اصلی آزاد است؛ بازنشر کامل بدون اجازه مجاز نیست.
- نمونه‌کدهای داخل آموزش‌ها را می‌توانید آزادانه در پروژه‌های خودتان به کار ببرید.

## محدودیت مسئولیت

محتوای سایت برای آموزش و اطلاع‌رسانی است. ما برای درستی مطالب تلاش می‌کنیم، اما مسئولیت استفاده از
آن‌ها، به‌ویژه اجرای کدها و تنظیمات امنیتی روی سیستم‌های واقعی، با خود شماست.

## تغییر قوانین

این قوانین ممکن است به‌روزرسانی شوند. ادامهٔ استفاده از سایت به معنای پذیرش نسخهٔ جدید است."""),
]

# Starting feeds for automatic AI Daily drafts; edit them in the admin.
NEWS_SOURCES = [
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/"),
    ("arXiv cs.CL", "https://rss.arxiv.org/rss/cs.CL"),
]

DEMO_BODY = """## مقدمه

این یک مطلب نمونه است که برای نمایش امکانات مجله ساخته شده. متن مقاله با **Markdown** نوشته می‌شود و
فهرست مطالب به‌صورت خودکار از تیترها ساخته می‌شود.

## یک نمونه کد

```python
from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title
```

### نکات مهم

- کدها به‌صورت خودکار رنگ‌آمیزی می‌شوند.
- دکمه کپی روی هر بلوک کد وجود دارد.
- زمان مطالعه به‌صورت خودکار محاسبه می‌شود.

## جمع‌بندی

| ویژگی | وضعیت |
|-------|-------|
| فهرست مطالب | ✅ |
| رنگ‌آمیزی کد | ✅ |
"""

DEMO_ARTICLES = [
    # (title, category slug, content type, tags, featured, editor pick)
    ("راهنمای جامع مدل‌های زبانی بزرگ (LLM) برای توسعه‌دهندگان", "ai", "article", ["LLM", "AI"], True, False),
    ("شروع کار با Django REST Framework", "tutorials", "tutorial", ["Django", "Python", "API"], False, True),
    ("۱۰ نکته برای نوشتن کد پایتون تمیزتر", "programming", "article", ["Python", "Clean Code"], False, False),
    ("آسیب‌پذیری جدید در کتابخانه‌های محبوب متن‌باز کشف شد", "security", "news", ["Security", "Open Source"], False, False),
    ("HTMX: تعامل‌پذیری بدون فریم‌ورک‌های سنگین جاوااسکریپت", "web", "tutorial", ["HTMX", "Frontend"], False, True),
    ("بررسی Kubernetes 1.34: چه چیزهایی تغییر کرد؟", "cloud-devops", "review", ["Kubernetes", "DevOps"], False, False),
    ("معرفی ابزار هوش مصنوعی برای کدنویسی", "ai", "ai_tool", ["AI", "Developer Tools"], False, False),
    ("پروژه متن‌باز هفته: یک پایگاه‌داده برداری سبک", "database", "open_source", ["Open Source", "Vector DB"], False, False),
    ("مروری بر مقاله Attention Is All You Need", "research", "research", ["Transformer", "Research"], False, False),
    ("اصول رمزنگاری که هر برنامه‌نویس باید بداند", "security", "article", ["Security", "Cryptography"], False, False),
    ("بازار پردازنده‌های گرافیکی در سال جدید", "hardware", "news", ["GPU"], False, False),
    ("مدل جدید متن‌باز هوش مصنوعی معرفی شد", "ai", "ai_daily", ["AI", "LLM"], False, False),
    ("گفت‌وگو با یک مهندس یادگیری ماشین درباره آینده LLMها", "ai", "interview", ["AI", "LLM", "Interview"], False, False),
]

DEMO_INTERVIEW = [
    ("از کجا شروع کردید؟", "از برنامه‌نویسی پایتون شروع کردم و کم‌کم به یادگیری ماشین علاقه‌مند شدم."),
    ("مهم‌ترین مهارت یک مهندس ML چیست؟", "درک عمیق داده. مدل خوب بدون داده تمیز معنا ندارد."),
    ("توصیه شما به تازه‌کارها؟", "پروژه واقعی بسازید و کدتان را متن‌باز کنید."),
]


class Command(BaseCommand):
    help = "Seed categories and static pages (and demo content with --demo)."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Also create a demo author and sample articles.")

    @transaction.atomic
    def handle(self, *args, demo=False, **options):
        for order, (slug, icon, name, description, on_home) in enumerate(CATEGORIES):
            Category.objects.update_or_create(
                slug=slug,
                defaults={"icon": icon, "name": name, "description": description,
                          "order": order, "show_on_home": on_home},
            )
        for order, (slug, title, body) in enumerate(PAGES):
            Page.objects.get_or_create(slug=slug, defaults={"title": title, "body": body, "order": order})
        for name, url in NEWS_SOURCES:
            NewsSource.objects.get_or_create(feed_url=url, defaults={"name": name})
        ensure_roles()
        self.stdout.write(self.style.SUCCESS(
            f"{len(CATEGORIES)} categories, {len(PAGES)} pages, news sources and roles ready."))

        if demo:
            self._create_demo()

    def _create_demo(self):
        User = get_user_model()
        author, created = User.objects.get_or_create(
            username="editor",
            defaults={"first_name": "تیم", "last_name": "تحریریه", "is_author": True,
                      "bio": "تیم تحریریه مجله فناوری"},
        )
        if created:
            author.set_unusable_password()
            author.save()

        now = timezone.now()
        count = 0
        for i, (title, cat_slug, ctype, tag_names, featured, pick) in enumerate(DEMO_ARTICLES):
            if Article.objects.filter(title=title).exists():
                continue
            extra = {}
            if ctype == Article.ContentType.INTERVIEW:
                extra = {"interviewee_name": "مریم احمدی", "interviewee_title": "مهندس ارشد یادگیری ماشین"}
            if ctype == Article.ContentType.AI_DAILY:
                extra = {
                    "why_important": "مدل‌های متن‌باز رقابت را با مدل‌های تجاری نزدیک‌تر می‌کنند.",
                    "use_cases": "دستیار کدنویسی، خلاصه‌سازی متن و چت‌بات‌های سازمانی.",
                    "developer_impact": "امکان اجرای محلی مدل و کاهش هزینه‌های API برای توسعه‌دهندگان.",
                }
            article = Article.objects.create(
                title=title,
                category=Category.objects.get(slug=cat_slug),
                content_type=ctype,
                author=author,
                excerpt=f"خلاصه‌ای کوتاه درباره «{title}» که در کارت‌ها و نتایج جستجو نمایش داده می‌شود.",
                body=DEMO_BODY,
                status=Article.Status.PUBLISHED,
                published_at=now - timedelta(hours=i * 7),
                is_featured=featured,
                is_editor_pick=pick,
                **extra,
            )
            article.tags.set([Tag.objects.get_or_create(name=name)[0] for name in tag_names])
            if ctype == Article.ContentType.INTERVIEW:
                for order, (question, answer) in enumerate(DEMO_INTERVIEW):
                    InterviewQA.objects.create(article=article, question=question, answer=answer, order=order)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} demo articles created."))
