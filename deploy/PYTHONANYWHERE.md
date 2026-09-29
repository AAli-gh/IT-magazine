# راه‌اندازی روی PythonAnywhere

راهنمای انتشار مجله روی [PythonAnywhere](https://www.pythonanywhere.com) (حساب رایگان یا پولی).
در ادامه به‌جای `USERNAME` نام کاربری PythonAnywhere خودتان را بگذارید.

روی حساب رایگان:
- دیتابیس SQLite است (PostgreSQL فقط در حساب پولی).
- Redis نیست و کش در حافظه نگه داشته می‌شود.
- دسترسی اینترنت سرور محدود به سایت‌های مجاز است. ممکن است دریافت خبر از RSS، ساخت خودکار AI Daily و ارسال ایمیل با بعضی سرویس‌ها کار نکند.
- هر چند وقت یک بار باید از تب **Web** دکمهٔ تمدید را بزنید.

## ۱. دریافت کد و نصب پکیج‌ها

از تب **Consoles** یک **Bash** باز کنید:

```bash
git clone -b claude/elegant-goldberg-3crtqg https://github.com/AAli-gh/IT-magazine.git
cd IT-magazine
mkvirtualenv --python=python3.12 itmag
pip install --no-cache-dir -r requirements.txt
```

اگر مخزن خصوصی است، git نام کاربری و یک Personal Access Token گیت‌هاب (به‌جای رمز) می‌خواهد.
اگر `python3.12` نبود، بالاترین نسخهٔ ۳.۱۰ به بالا را بزنید.

## ۲. فایل تنظیمات `.env`

```bash
nano ~/IT-magazine/.env
```

```ini
DJANGO_SECRET_KEY=یک-رشته-طولانی-و-تصادفی
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=USERNAME.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://USERNAME.pythonanywhere.com
SITE_URL=https://USERNAME.pythonanywhere.com
DJANGO_SECURE_SSL_REDIRECT=False
ACCOUNT_EMAIL_VERIFICATION=optional
```

- برای ساخت `DJANGO_SECRET_KEY` این را اجرا کنید:
  `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- ریدایرکت به HTTPS را خود PythonAnywhere انجام می‌دهد (مرحلهٔ ۴). برای همین `DJANGO_SECURE_SSL_REDIRECT` خاموش است.
- برای ایمیل واقعی، متغیرهای `EMAIL_*` را طبق `.env.example` اضافه کنید.
- `DATABASE_URL` و `REDIS_URL` را نگذارید.

## ۳. دیتابیس و فایل‌های استاتیک

```bash
cd ~/IT-magazine
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_magazine --demo   # بدون --demo: فقط دسته‌ها، صفحات و نقش‌ها بدون مطالب نمونه
python manage.py createsuperuser
```

## ۴. ساخت وب‌اپ

در تب **Web**:

1. **Add a new web app** → **Manual configuration** (نه گزینهٔ Django) → همان نسخهٔ پایتون مرحلهٔ ۱.
2. **Virtualenv:** `/home/USERNAME/.virtualenvs/itmag`
3. **Source code** و **Working directory:** `/home/USERNAME/IT-magazine`
4. روی لینک **WSGI configuration file** بزنید، همهٔ محتوایش را پاک کنید و این را بگذارید:

   ```python
   import os
   import sys

   path = "/home/USERNAME/IT-magazine"
   if path not in sys.path:
       sys.path.insert(0, path)
   os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

5. در بخش **Static files**:

   | URL | Directory |
   |---|---|
   | `/static/` | `/home/USERNAME/IT-magazine/staticfiles` |
   | `/media/` | `/home/USERNAME/IT-magazine/media` |

6. **Force HTTPS** را روشن کنید.
7. دکمهٔ سبز **Reload** را بزنید و `https://USERNAME.pythonanywhere.com` را باز کنید.

## ۵. ورود به پنل ادمین

`/admin/` شما را به صفحهٔ ورود سایت می‌برد. بعد از ورود، چون `DEBUG=False` است، اول باید ورود دومرحله‌ای را فعال کنید (با Google Authenticator یا هر برنامهٔ مشابه). بعد پنل باز می‌شود.

## ۶. کارهای زمان‌بندی‌شده

در تب **Tasks** این دستور را اضافه کنید:

```bash
/home/USERNAME/.virtualenvs/itmag/bin/python /home/USERNAME/IT-magazine/manage.py run_scheduler --once
```

این دستور هر بار که اجرا شود کارهای موعدرسیده را انجام می‌دهد: اعلان‌ها، AI Daily و خبرنامه.
- حساب رایگان: یک کار روزانه. ساعت Tasks به وقت UTC است. **07:00 UTC** (۱۰:۳۰ تهران) را بزنید تا بعد از ساخت و ارسال AI Daily و خبرنامهٔ هفتگی جمعه‌ها اجرا شود.
- حساب پولی: می‌توانید آن را هر ساعت اجرا کنید.

## به‌روزرسانی بعد از تغییر کد

```bash
cd ~/IT-magazine && workon itmag
git pull
pip install --no-cache-dir -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

بعد در تب **Web** دکمهٔ **Reload** را بزنید.

## اشکال‌یابی

اگر سایت خطا داد، **Error log** را در تب **Web** ببینید.
رایج‌ترین علت‌ها:
- اشتباه در `DJANGO_ALLOWED_HOSTS`
- اجرا نکردن `migrate` یا `collectstatic`
- اشتباه در مسیرهای WSGI
