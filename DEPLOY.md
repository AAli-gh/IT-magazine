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

## به‌روزرسانی

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## پشتیبان‌گیری

```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U itmag itmag | gzip > backup-$(date +%F).sql.gz
docker run --rm -v itmag_media:/media -v "$PWD":/backup alpine tar czf /backup/media-$(date +%F).tgz -C /media .
```

## نکات

- `/healthz` برای مانیتورینگ است (Docker healthcheck از آن استفاده می‌کند).
- HSTS به‌صورت پیش‌فرض ۳۰ روز است (`SECURE_HSTS_SECONDS`).
- حداکثر حجم آپلود در Nginx ۶۰۰ مگابایت است (برای ویدئو)؛ در `deploy/nginx.conf.template` قابل تغییر است.
- افزونه `pg_trgm` در مایگریشن فعال می‌شود؛ کاربر دیتابیس باید مالک دیتابیس باشد (در PostgreSQL 13+ کافی است).
