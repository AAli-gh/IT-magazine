# مجله فناوری | IT Magazine

مجله فارسی (راست‌به‌چپ) برای مقاله، خبر و آموزش در حوزه‌های هوش مصنوعی، برنامه‌نویسی، توسعه وب، امنیت، Cloud/DevOps و سایر موضوعات IT.

**استک:** Python · Django 5.2 · Django REST Framework · PostgreSQL · Tailwind CSS · HTMX · Vanilla JS

## امکانات

- **صفحه اصلی:** مهم‌ترین مطلب روز، جدیدترین مطالب، بخش‌های دسته‌بندی (AI، برنامه‌نویسی، امنیت — از طریق «نمایش در صفحه اصلی» در پنل قابل تنظیم است)، آموزش‌های منتخب، آخرین اخبار، پربازدیدترین‌ها، باکس AI Daily
- **۱۳ دسته‌بندی** و **۱۱ نوع محتوا:** مقاله، خبر، آموزش، بررسی، ابزار AI، پروژه Open Source، مقاله علمی، مصاحبه، ویدئو (با embed یوتیوب/آپارات)، پادکست، AI Daily
- **صفحه مقاله:** تصویر اصلی، نویسنده، زمان مطالعه (محاسبه خودکار)، تاریخ شمسی، فهرست مطالب خودکار از تیترها، رنگ‌آمیزی کد با دکمه کپی، نوار پیشرفت مطالعه، تگ‌ها، مطالب مرتبط، دیدگاه و پاسخ، اشتراک‌گذاری
- **AI Daily:** شماره‌گذاری خودکار (`AI Daily #127`) با سه بخش «چرا مهم است؟»، «چه کاربردی دارد؟» و «چه تأثیری روی توسعه‌دهندگان دارد؟» — آرشیو در `/ai-daily/` و لینک کوتاه `/ai-daily/<شماره>/`
- **کاربران:** ثبت‌نام/ورود، پروفایل، ذخیره، لایک، دیدگاه، دنبال کردن موضوعات (فید شخصی)، تاریخچه مطالعه
- **جستجوی پیشرفته:** فیلتر دسته‌بندی، نوع محتوا، تگ و مرتب‌سازی، با نتایج زنده (HTMX)
- **SEO:** عنوان/توضیحات SEO برای هر مطلب، Open Graph، JSON-LD، canonical، `sitemap.xml`، `robots.txt`، RSS کلی و RSS هر دسته
- **پنل مدیریت:** Django Admin سفارشی برای مطالب، نویسندگان، دسته‌بندی‌ها، تگ‌ها، کاربران، دیدگاه‌ها (تأیید گروهی)، بنرها و تبلیغات (با زمان‌بندی و جایگاه)، صفحات سایت
- **API:** `/api/articles/` (فیلترهای `q`، `category`، `type`، `tag`)، `/api/categories/`، `/api/tags/`
- تم تیره/روشن، طراحی واکنش‌گرا، **بدون وابستگی به CDN** (فونت وزیرمتن و HTMX داخل پروژه هستند)

## راه‌اندازی

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # اختیاری؛ بدون DATABASE_URL از SQLite استفاده می‌شود
python manage.py migrate
python manage.py seed_magazine --demo   # دسته‌بندی‌ها، صفحات و چند مطلب نمونه
python manage.py createsuperuser
python manage.py runserver
```

برای PostgreSQL متغیر `DATABASE_URL` را تنظیم کنید، یا با Docker:

```bash
docker compose up --build
docker compose exec web python manage.py seed_magazine --demo
```

## فرانت‌اند (Tailwind)

فایل CSS ساخته‌شده (`static/css/tailwind.css`) در مخزن هست، پس برای اجرا به Node نیازی ندارید. فقط اگر کلاس‌های قالب‌ها را تغییر دادید دوباره build کنید:

```bash
npm install
npm run build       # vendor کردن HTMX و فونت + ساخت CSS
npm run watch:css   # حین توسعه
```

## ساختار پروژه

| مسیر | توضیح |
|------|-------|
| `config/` | تنظیمات و URLها |
| `magazine/` | مطالب، دسته‌بندی‌ها، تگ‌ها، AI Daily، جستجو، RSS، sitemap و API |
| `accounts/` | مدل کاربر سفارشی، ثبت‌نام، پروفایل و صفحه نویسنده |
| `interactions/` | لایک، ذخیره، دیدگاه، دنبال کردن موضوع، تاریخچه (endpointهای HTMX) |
| `core/` | صفحات ثابت، بنرها و تبلیغات، context processor و template tagها |
| `templates/` | قالب‌ها |
| `assets/`, `static/` | سورس Tailwind و فایل‌های استاتیک |

## تست

```bash
python manage.py test
```

## قدم‌های بعدی

- سیستم پیشنهاد مقاله با AI
- جستجوی هوشمند (Full-text search در PostgreSQL / جستجوی برداری)
- ویرایشگر Markdown با پیش‌نمایش در پنل
