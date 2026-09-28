# استقرار روی سرور

این راهنما یک سرور لینوکس (مثلاً Ubuntu) با Docker و یک دامنه که به IP سرور اشاره می‌کند را فرض می‌کند.

## ۱. آماده‌سازی

```bash
git clone <repo-url> itmag && cd itmag
cp .env.example .env
```

فایل `.env` را پر کنید؛ حداقل:

- `DJANGO_SECRET_KEY` — یک رشته تصادفی طولانی: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
- `DOMAIN`، `DJANGO_ALLOWED_HOSTS`، `DJANGO_CSRF_TRUSTED_ORIGINS`، `SITE_URL`
- `POSTGRES_PASSWORD` و همان رمز در `DATABASE_URL`
- تنظیمات SMTP (`EMAIL_HOST` و...) برای ایمیل تأیید، بازیابی رمز و خبرنامه
- اختیاری: `ANTHROPIC_API_KEY`، کلیدهای OAuth گوگل/گیت‌هاب

## ۲. گواهی HTTPS (فقط بار اول)

```bash
sh deploy/init-letsencrypt.sh you@example.com
```

این اسکریپت Nginx را با یک گواهی موقت بالا می‌آورد، گواهی واقعی Let's Encrypt را می‌گیرد و Nginx را reload می‌کند. سرویس `certbot` گواهی را هر ۱۲ ساعت تمدید می‌کند.

## ۳. اجرا

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py seed_magazine
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

سرویس‌ها:

| سرویس | نقش |
|---|---|
| `nginx` | HTTPS، فایل‌های static/media، پروکسی به Gunicorn |
| `web` | Django + Gunicorn (مایگریشن خودکار در شروع) |
| `scheduler` | `run_scheduler`: اعلان‌ها، AI Daily، خبرنامه |
| `db` | PostgreSQL 16 |
| `redis` | کش |
| `certbot` | تمدید گواهی |
| `backup` | پشتیبان‌گیری روزانه دیتابیس و فایل‌های آپلودی در پوشه `backups/` |

## ورود دومرحله‌ای پنل مدیریت (2FA)

در حالت production (`DJANGO_DEBUG=False`) هر کاربر کادر (نویسنده، سردبیر، مدیر) قبل از ورود به `/admin/` باید ورود دومرحله‌ای را با یک اپ Authenticator (مثل Google Authenticator یا Aegis) فعال کند؛ سایت خودش او را به صفحه فعال‌سازی می‌برد. ورود به پنل هم از صفحه ورود سایت انجام می‌شود تا کد دومرحله‌ای و محدودیت تلاش ناموفق اعمال شود.

- کدهای بازیابی را بعد از فعال‌سازی جایی امن نگه دارید.
- اگر مدیری دسترسی به گوشی و کدهای بازیابی را از دست داد، مدیر دیگری می‌تواند در پنل، بخش «Authenticators» رکورد او را حذف کند تا دوباره فعال‌سازی کند.
- برای خاموش کردن اجبار (توصیه نمی‌شود): `ADMIN_REQUIRE_MFA=False`

## گزارش خطا

- **ایمیل:** `DJANGO_ADMINS` را تنظیم کنید (مثلاً `Ali:ali@example.com`)؛ هر خطای ۵۰۰ با جزئیات برایشان ایمیل می‌شود (SMTP لازم است).
- **Sentry / GlitchTip:** `SENTRY_DSN` را تنظیم کنید. اگر Sentry در دسترس نیست، [GlitchTip](https://glitchtip.com) نسخه متن‌باز و قابل نصب روی سرور خودتان با همان DSN است. اطلاعات شخصی کاربران ارسال نمی‌شود (`send_default_pii=False`).
- کاربر در صورت خطا صفحه ۵۰۰ اختصاصی می‌بیند که به دیتابیس وابسته نیست.

## پشتیبان‌گیری

سرویس `backup` هر ۲۴ ساعت یک `pg_dump` فشرده و یک آرشیو از فایل‌های آپلودی در پوشه `backups/` کنار پروژه می‌سازد و نسخه‌های قدیمی‌تر از `BACKUP_KEEP_DAYS` روز (پیش‌فرض ۱۴) را پاک می‌کند.

```bash
# پشتیبان فوری
docker compose -f docker-compose.prod.yml run --rm backup sh /backup.sh --once
ls backups/
```

**بازگردانی:**

```bash
gunzip -c backups/db-2026-01-01.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U itmag itmag
docker compose -f docker-compose.prod.yml run --rm -v "$PWD/backups":/restore backup sh -c "tar xzf /restore/media-2026-01-01.tgz -C /media"
```

> پشتیبانی که روی همان سرور بماند در برابر خرابی دیسک یا از دست رفتن سرور کمکی نمی‌کند. پوشه `backups/` را منظم به جای دیگری کپی کنید، مثلاً با `rclone copy backups/ remote:itmag-backups` در یک cron روزانه.

## به‌روزرسانی

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## نکات

- `/healthz` برای مانیتورینگ است (Docker healthcheck از آن استفاده می‌کند).
- HSTS به‌صورت پیش‌فرض ۳۰ روز است (`SECURE_HSTS_SECONDS`).
- **سقف حجم آپلود:** ویدئو `MAX_VIDEO_UPLOAD_MB` (۵۰۰)، صوت `MAX_AUDIO_UPLOAD_MB` (۲۰۰)، تصویر `MAX_IMAGE_UPLOAD_MB` (۱۰). سقف کلی Nginx ۶۰۰ مگابایت است؛ اگر سقف ویدئو را بالا بردید، `client_max_body_size` در `deploy/nginx.conf.template` را هم بیشتر کنید.
- افزونه `pg_trgm` و ایندکس جستجوی تمام‌متن (GIN) در مایگریشن ساخته می‌شوند؛ کاربر دیتابیس باید مالک دیتابیس باشد (در PostgreSQL 13+ کافی است). locale دیتابیس باید UTF-8 باشد (پیش‌فرض ایمیج رسمی postgres) تا کلمات فارسی درست شکسته شوند.
