"""Fourth batch, part four: tutorials 16–30."""

FRESH_TUTORIALS_B = [
    dict(
        title="Generator و Iterator در پایتون: پردازش داده‌های بزرگ با حافظهٔ کم",
        category="programming", type="tutorial", tags=["Python", "Generator", "Performance"], label="GENERATORS",
        photo="1619410283995-43d9134e7656",
        excerpt="خواندن یک فایل لاگ ده‌گیگابایتی بدون پر کردن RAM؟ با yield، داده را تکه‌تکه و فقط هنگام نیاز تولید "
                "کنید.",
        body=r"""## مشکل

```python
def read_lines(path):
    with open(path) as f:
        return f.readlines()   # کل فایل یکجا در حافظه!
```

برای فایل چند گیگابایتی، این کد حافظه را پر می‌کند.

## Generator با yield

```python
def read_lines(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")

for line in read_lines("access.log"):
    if " 500 " in line:
        print(line)
```

تابعی که `yield` دارد، با صدا زدن اجرا نمی‌شود؛ یک **generator** برمی‌گرداند. هر بار که مقدار بعدی خواسته شود،
تابع تا `yield` بعدی جلو می‌رود و همان‌جا **متوقف** می‌ماند.

```python
def count_up(n):
    i = 1
    while i <= n:
        yield i
        i += 1

gen = count_up(3)
next(gen)  # 1
next(gen)  # 2
list(gen)  # [3]
```

## Generator Expression

مثل list comprehension، اما با پرانتز:

```python
squares_list = [x * x for x in range(10_000_000)]   # ده میلیون عدد در حافظه
squares_gen = (x * x for x in range(10_000_000))    # تقریباً بدون حافظه
total = sum(x * x for x in range(10_000_000))
```

## زنجیره‌سازی (Pipeline)

```python
def parse(lines):
    # قالب رایج لاگ: IP - - [زمان] "GET /path HTTP/1.1" وضعیت حجم
    for line in lines:
        parts = line.split()
        yield {"ip": parts[0], "status": parts[8]}

def only_errors(records):
    return (r for r in records if r["status"].startswith("5"))

errors = only_errors(parse(read_lines("access.log")))
for record in errors:
    print(record["ip"])
```

هر ردیف یکی‌یکی از کل زنجیره عبور می‌کند؛ هیچ مرحله‌ای کل داده را در حافظه نگه نمی‌دارد.

## yield from

```python
def walk(tree):
    yield tree.value
    for child in tree.children:
        yield from walk(child)
```

## itertools: جعبه‌ابزار

```python
from itertools import islice, chain, batched

first_10 = list(islice(read_lines("big.log"), 10))
all_lines = chain(read_lines("a.log"), read_lines("b.log"))
for batch in batched(read_lines("ids.txt"), 1000):   # پایتون ۳.۱۲ به بعد
    insert_many(batch)
```

## Iterator چیست؟

هر شیئی که متد `__next__` دارد و در پایان `StopIteration` می‌دهد. generatorها ساده‌ترین راه ساخت iterator هستند.
شیئی که `__iter__` دارد (مثل لیست) **iterable** است و می‌شود از آن iterator گرفت.

## یک دام

generator فقط **یک بار** پیمایش می‌شود:

```python
gen = (x for x in range(3))
list(gen)  # [0, 1, 2]
list(gen)  # []
```

اگر چند بار به داده نیاز دارید، یا آن را در لیست ذخیره کنید یا generator را دوباره بسازید.
""",
    ),
    dict(
        title="اعتبارسنجی داده با Pydantic: دیگر به ورودی اعتماد نکنید",
        category="programming", type="tutorial", tags=["Pydantic", "Python", "Validation"], label="PYDANTIC",
        photo="1581091226825-a6a2a5aee158",
        excerpt="دادهٔ ورودی از API، فایل JSON یا متغیرهای محیطی همیشه آن چیزی نیست که انتظار دارید. با Pydantic و type "
                "hint، داده را در مرز برنامه بررسی و تبدیل کنید.",
        body=r"""## نصب

```bash
pip install pydantic
pip install "pydantic[email]"   # برای EmailStr
```

این آموزش بر اساس **Pydantic نسخهٔ ۲** است.

## اولین مدل

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    is_active: bool = True

user = User(id="42", name="Sara")
print(user.id, type(user.id))   # 42 <class 'int'>
```

Pydantic رشتهٔ `"42"` را به عدد تبدیل کرد. اما اگر تبدیل ممکن نباشد:

```python
from pydantic import ValidationError

try:
    User(id="abc", name="Sara")
except ValidationError as e:
    print(e)
# id: Input should be a valid integer, unable to parse string as an integer
```

## محدودیت‌ها با Field

```python
from pydantic import BaseModel, EmailStr, Field

class SignUp(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    email: EmailStr
    age: int = Field(ge=13, le=120)
    tags: list[str] = []
```

## اعتبارسنج سفارشی

```python
from pydantic import field_validator, model_validator

class ChangePassword(BaseModel):
    password: str
    password_confirm: str

    @field_validator("password")
    @classmethod
    def strong_enough(cls, value):
        if len(value) < 12:
            raise ValueError("رمز باید حداقل ۱۲ کاراکتر باشد")
        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("رمزها یکسان نیستند")
        return self
```

## مدل‌های تودرتو

```python
class Address(BaseModel):
    city: str
    postal_code: str

class Customer(BaseModel):
    name: str
    addresses: list[Address]

data = {"name": "Reza", "addresses": [{"city": "Shiraz", "postal_code": "71234"}]}
customer = Customer.model_validate(data)
```

## تبدیل به dict و JSON

```python
customer.model_dump()
customer.model_dump_json(indent=2)
```

## تنظیمات برنامه از متغیرهای محیطی

```python
# pip install pydantic-settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    debug: bool = False
    max_upload_mb: int = 10

settings = Settings()   # از متغیرهای DATABASE_URL، DEBUG و MAX_UPLOAD_MB می‌خواند
```

اگر متغیر الزامی تنظیم نشده باشد، برنامه **هنگام شروع** با پیام روشن متوقف می‌شود، نه وسط کار و در محیط
production.

## اصل کلی

داده را **در مرز** برنامه (درخواست API، خواندن فایل، پیام صف) اعتبارسنجی کنید. از آن به بعد، بقیهٔ کد می‌تواند به
نوع داده اعتماد کند.
""",
    ),
    dict(
        title="لاگ‌نویسی درست در پایتون با ماژول logging",
        category="programming", type="tutorial", tags=["Python", "Logging", "Debugging"], label="LOGGING",
        photo="1608306448197-e83633f1261c",
        excerpt="`print` برای دیباگ سریع خوب است، اما در production کمکی نمی‌کند. با ماژول logging پیام‌ها را با سطح، "
                "زمان و محل ثبت کنید و بدانید چه چیزی را نباید لاگ کرد.",
        body=r"""## چرا print کافی نیست؟

- نمی‌شود پیام‌ها را بر اساس اهمیت فیلتر کرد.
- زمان، ماژول و شمارهٔ خط ثبت نمی‌شود.
- نمی‌شود خروجی را بدون تغییر کد به فایل یا سرویس دیگری فرستاد.

## شروع سریع

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logger.info("Server started on port %s", 8000)
```

## سطح‌ها

| سطح | کاربرد |
|---|---|
| `DEBUG` | جزئیات برای عیب‌یابی |
| `INFO` | رویدادهای عادی: شروع سرویس، پایان یک کار |
| `WARNING` | اتفاقی غیرعادی که فعلاً مشکلی ایجاد نکرده |
| `ERROR` | عملیاتی شکست خورد |
| `CRITICAL` | کل برنامه در خطر است |

## یک logger برای هر ماژول

```python
logger = logging.getLogger(__name__)
```

نام logger همان مسیر ماژول (مثل `shop.payments`) می‌شود و می‌توانید سطح هر بخش را جداگانه تنظیم کنید.

## قالب‌بندی تنبل

```python
logger.debug("User %s loaded %d items", user_id, len(items))   # درست
logger.debug(f"User {user_id} loaded {len(items)} items")      # کار می‌کند، اما رشته حتی وقتی DEBUG خاموش است ساخته می‌شود
```

## ثبت خطا همراه با Traceback

```python
try:
    process_payment(order)
except PaymentError:
    logger.exception("Payment failed for order %s", order.id)
    raise
```

`logger.exception` باید داخل بلوک `except` صدا زده شود و traceback کامل را به‌طور خودکار اضافه می‌کند.

## تنظیم در جنگو

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.db.backends": {"level": "WARNING"},
    },
}
```

در محیط‌های کانتینری، بهترین روش نوشتن لاگ روی **خروجی استاندارد** است تا Docker یا systemd جمع‌آوری آن را
انجام دهند.

## چه چیزهایی را لاگ نکنیم؟

- رمز عبور، توکن، کلید API و کوکی session
- اطلاعات کامل کارت بانکی
- اطلاعات شخصی بیش از حد نیاز

```python
logger.info("Login attempt for %s", username)   # خوب
logger.info("Login: %s / %s", username, password)   # هرگز!
```

## لاگ ساخت‌یافته

برای جست‌وجو در ابزارهایی مثل Grafana Loki یا Elasticsearch، لاگ را به شکل JSON بنویسید؛ بسته‌هایی مثل
`python-json-logger` یا `structlog` این کار را ساده می‌کنند.
""",
    ),
    dict(
        title="Docker از صفر: اولین Dockerfile و کانتینر",
        category="cloud-devops", type="tutorial", tags=["Docker", "Container", "DevOps"], label="DOCKER", photo="1614741118887-7a4ee193a5fa",
        excerpt="«روی سیستم من کار می‌کند!» با Docker برنامه و همهٔ وابستگی‌هایش در یک بستهٔ قابل حمل قرار می‌گیرد. مفاهیم "
                "پایه و دستورهای اصلی را یاد بگیرید.",
        body=r"""## سه مفهوم اصلی

| مفهوم | توضیح | شبیه |
|---|---|---|
| Image | قالب فقط‌خواندنی شامل سیستم‌فایل و برنامه | کلاس |
| Container | نمونهٔ در حال اجرا از یک image | شیء |
| Registry | انبار imageها، مثل Docker Hub | مخزن بسته‌ها |

کانتینر ماشین مجازی نیست؛ از هستهٔ سیستم‌عامل میزبان استفاده می‌کند و برای همین در کسری از ثانیه بالا می‌آید.

## اولین اجرا

```bash
docker run --rm hello-world
docker run --rm -it python:3.13-slim python
```

## Dockerfile برای یک برنامهٔ پایتون

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### چرا requirements.txt جدا کپی شد؟

Docker هر دستور را یک **لایه** می‌کند و لایه‌ها را کش می‌کند. چون وابستگی‌ها کمتر از کد عوض می‌شوند، با این ترتیب
تغییر کد باعث نصب دوبارهٔ همهٔ بسته‌ها نمی‌شود.

## .dockerignore

```text
.git
.venv
__pycache__
*.sqlite3
.env
node_modules
```

بدون این فایل، رمزها و فایل‌های حجیم وارد image می‌شوند.

## ساخت و اجرا

```bash
docker build -t mysite:1.0 .
docker run -d --name mysite -p 8000:8000 --env-file .env mysite:1.0
```

`-p 8000:8000` پورت ۸۰۰۰ میزبان را به پورت ۸۰۰۰ کانتینر وصل می‌کند.

## دستورهای روزمره

| دستور | کاربرد |
|---|---|
| `docker ps` / `docker ps -a` | کانتینرهای در حال اجرا / همه |
| `docker logs -f mysite` | دیدن لاگ‌ها |
| `docker exec -it mysite bash` | ورود به داخل کانتینر |
| `docker stop mysite` / `docker rm mysite` | توقف / حذف |
| `docker images` | فهرست imageها |
| `docker system prune` | پاک‌سازی موارد بلااستفاده |

## داده‌ها کجا بمانند؟

با حذف کانتینر، هر چیزی که درون آن نوشته شده از بین می‌رود. برای دادهٔ ماندگار از **Volume** استفاده کنید:

```bash
docker volume create pgdata
docker run -d -v pgdata:/var/lib/postgresql/data -e POSTGRES_PASSWORD=secret postgres:17
```

## قدم بعدی

وقتی برنامه به چند کانتینر (وب، دیتابیس، Redis) نیاز دارد، از **Docker Compose** استفاده کنید و برای image
کوچک‌تر سراغ **multi-stage build** بروید.
""",
    ),
    dict(
        title="زمان‌بندی کارها در لینوکس با cron و systemd timer",
        category="tutorials", type="tutorial", tags=["Linux", "cron", "Automation"], label="CRON", photo="1640552435388-a54879e72b28",
        excerpt="پشتیبان‌گیری شبانه، پاک کردن فایل‌های موقت یا ارسال گزارش هفتگی؛ کارهای تکراری را به سیستم‌عامل بسپارید.",
        body=r"""## cron: زمان‌بند کلاسیک

هر کاربر یک **crontab** دارد:

```bash
crontab -e    # ویرایش
crontab -l    # نمایش
```

## قالب یک خط

```text
┌──────── دقیقه (0-59)
│ ┌────── ساعت (0-23)
│ │ ┌──── روز ماه (1-31)
│ │ │ ┌── ماه (1-12)
│ │ │ │ ┌ روز هفته (0-7؛ ۰ و ۷ هر دو یکشنبه)
│ │ │ │ │
* * * * *  دستور
```

## مثال‌ها

| عبارت | معنی |
|---|---|
| `0 3 * * *` | هر روز ساعت ۳ بامداد |
| `*/15 * * * *` | هر ۱۵ دقیقه |
| `30 9 * * 1-5` | دوشنبه تا جمعه ساعت ۹:۳۰ |
| `0 0 1 * *` | اول هر ماه، نیمه‌شب |
| `@reboot` | یک بار بعد از هر راه‌اندازی |

```text
0 3 * * * /home/deploy/backup.sh >> /home/deploy/logs/backup.log 2>&1
```

## دام‌های رایج cron

1. **محیط متفاوت:** cron متغیرهای محیطی و `PATH` شما را ندارد. از **مسیر کامل** دستورها استفاده کنید:
   `/srv/mysite/.venv/bin/python /srv/mysite/manage.py clearsessions`
2. **خروجی گم می‌شود:** بدون `>> file 2>&1`، خطاها دیده نمی‌شوند.
3. **علامت `%`:** در crontab معنای خاص دارد و باید به شکل `\%` نوشته شود؛ مثلاً در `date +\%F`.
4. **منطقهٔ زمانی:** cron با ساعت سیستم کار می‌کند؛ ساعت سرور را با `timedatectl` بررسی کنید.

## اجرای هم‌زمان را مهار کنید

اگر کار قبلی هنوز تمام نشده، نسخهٔ جدید نباید شروع شود:

```text
*/5 * * * * flock -n /tmp/sync.lock /home/deploy/sync.sh
```

## systemd timer: جایگزین مدرن

دو فایل لازم است. `/etc/systemd/system/backup.service`:

```ini
[Unit]
Description=Nightly backup

[Service]
Type=oneshot
User=deploy
ExecStart=/home/deploy/backup.sh
```

و `/etc/systemd/system/backup.timer`:

```ini
[Unit]
Description=Run backup nightly

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now backup.timer
systemctl list-timers
journalctl -u backup.service
```

## مقایسه

| | cron | systemd timer |
|---|---|---|
| سادگی | یک خط | دو فایل |
| لاگ | دستی | خودکار در journal |
| اجرای کارهای جامانده هنگام خاموشی | ندارد | با `Persistent=true` |
| کنترل منابع و وابستگی‌ها | ندارد | دارد |

برای کارهای ساده cron کافی است؛ برای کارهای مهم روی سرور، systemd timer کنترل و دیدپذیری بیشتری می‌دهد.
""",
    ),
    dict(
        title="Vim برای بقا: ویرایش فایل روی سرور بدون وحشت",
        category="tutorials", type="tutorial", tags=["Vim", "Linux", "Terminal"], label="VIM", photo="1516259762381-22954d7d3ad2",
        excerpt="دیر یا زود روی سروری خواهید بود که فقط Vim دارد. حداقل دستورهایی که برای باز کردن، ویرایش، ذخیره و "
                "خروج لازم دارید.",
        body=r"""## مهم‌ترین نکته: Vim حالت دارد

| حالت | کاربرد | ورود |
|---|---|---|
| Normal | حرکت و دستورها | `Esc` |
| Insert | تایپ متن | `i` |
| Visual | انتخاب متن | `v` |
| Command | ذخیره، خروج، جست‌وجو و جایگزینی | `:` |

اگر نمی‌دانید در کدام حالت هستید، **دو بار `Esc`** بزنید؛ به حالت Normal برمی‌گردید.

## خروج (مشهورترین سؤال)

| دستور | کار |
|---|---|
| `:w` | ذخیره |
| `:q` | خروج |
| `:wq` یا `:x` | ذخیره و خروج |
| `:q!` | خروج بدون ذخیره |

## ورود به حالت تایپ

| کلید | محل شروع تایپ |
|---|---|
| `i` | قبل از مکان‌نما |
| `a` | بعد از مکان‌نما |
| `o` | خط جدید زیر خط فعلی |
| `O` | خط جدید بالای خط فعلی |

## حرکت

| کلید | حرکت |
|---|---|
| `h j k l` | چپ، پایین، بالا، راست (کلیدهای جهت‌نما هم کار می‌کنند) |
| `w` / `b` | کلمهٔ بعد / قبل |
| `0` / `$` | ابتدا / انتهای خط |
| `gg` / `G` | ابتدا / انتهای فایل |
| `:42` | رفتن به خط ۴۲ |

## ویرایش در حالت Normal

| دستور | کار |
|---|---|
| `x` | حذف یک کاراکتر |
| `dd` | حذف (برش) خط |
| `yy` | کپی خط |
| `p` | چسباندن |
| `u` | بازگردانی (undo) |
| `Ctrl+r` | انجام دوباره (redo) |
| `ciw` | پاک کردن کلمه و رفتن به حالت تایپ |
| `.` | تکرار آخرین تغییر |

دستورها با عدد ترکیب می‌شوند: `3dd` سه خط را حذف می‌کند.

## جست‌وجو و جایگزینی

```text
/DEBUG          جست‌وجو؛ n بعدی و N قبلی
:%s/old/new/g   جایگزینی در کل فایل
:%s/old/new/gc  جایگزینی با پرسیدن تأیید برای هر مورد
```

## سناریوی واقعی: تغییر یک تنظیم

```bash
sudo vim /etc/nginx/sites-available/mysite
```

1. `/server_name` و `Enter` برای پیدا کردن خط
2. `w` برای رفتن روی مقدار، `ciw` و تایپ مقدار جدید
3. `Esc` و سپس `:wq`
4. `sudo nginx -t` برای بررسی

## یادگیری بیشتر

دستور `vimtutor` را در ترمینال اجرا کنید؛ آموزش تعاملی حدوداً نیم‌ساعته‌ای است که همراه Vim نصب می‌شود. اگر Vim
را دوست نداشتید، ویرایشگر **nano** ساده‌تر است و راهنمای کلیدهایش پایین صفحه نمایش داده می‌شود.
""",
    ),
    dict(
        title="VS Code حرفه‌ای: میانبرها، تنظیمات و افزونه‌های ضروری",
        category="tutorials", type="tutorial", tags=["VS Code", "Productivity", "Editor"], label="VS CODE",
        photo="1607705703571-c5a8695f18f6",
        excerpt="بیشتر برنامه‌نویس‌ها فقط بخش کوچکی از توانایی‌های VS Code را استفاده می‌کنند. با چند میانبر و تنظیم، "
                "هر روز دقیقه‌ها صرفه‌جویی کنید.",
        body=r"""## میانبرهای ضروری

کلیدها برای ویندوز و لینوکس است؛ در macOS به‌جای `Ctrl` از `Cmd` استفاده کنید.

| میانبر | کار |
|---|---|
| `Ctrl+P` | باز کردن سریع فایل با تایپ بخشی از نام |
| `Ctrl+Shift+P` | پالت فرمان؛ دسترسی به همهٔ دستورها |
| ``Ctrl+` `` | باز و بسته کردن ترمینال |
| `Ctrl+B` | نمایش / پنهان کردن نوار کناری |
| `Ctrl+Shift+F` | جست‌وجو در کل پروژه |
| `Ctrl+/` | توضیح کردن (comment) خط |
| `Alt+↑` / `Alt+↓` | جابه‌جا کردن خط |
| `Shift+Alt+↓` | تکثیر خط |
| `F12` | رفتن به تعریف |
| `Shift+F12` | یافتن همهٔ ارجاع‌ها |
| `F2` | تغییر نام نماد در همهٔ فایل‌ها |
| `Ctrl+.` | پیشنهادهای اصلاح سریع |

## چند مکان‌نما

- `Ctrl+D`: انتخاب مورد بعدی از کلمهٔ انتخاب‌شده؛ چند بار بزنید و هم‌زمان همه را ویرایش کنید.
- `Alt+Click`: گذاشتن مکان‌نمای اضافه در هر جا.
- `Ctrl+Shift+L`: انتخاب همهٔ موارد مشابه.

## تنظیمات پیشنهادی

پالت فرمان ← «Preferences: Open User Settings (JSON)»:

```json
{
  "editor.formatOnSave": true,
  "editor.rulers": [100],
  "editor.minimap.enabled": false,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "editor.fontFamily": "Fira Code, Consolas, monospace"
}
```

## تنظیمات مخصوص پروژه

فایل `.vscode/settings.json` در ریشهٔ پروژه، تنظیمات را برای همهٔ اعضای تیم یکسان می‌کند:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "[python]": { "editor.defaultFormatter": "charliermarsh.ruff" }
}
```

## افزونه‌های پرکاربرد

| افزونه | کاربرد |
|---|---|
| Python و Pylance | تکمیل کد، بررسی نوع و دیباگ پایتون |
| Ruff | lint و فرمت سریع پایتون |
| ESLint و Prettier | کیفیت و فرمت کد جاوااسکریپت |
| GitLens | تاریخچهٔ هر خط و نویسندهٔ آن |
| Docker | مدیریت کانتینرها و imageها |
| Remote - SSH | ویرایش فایل‌های سرور مثل فایل محلی |
| Tailwind CSS IntelliSense | پیشنهاد کلاس‌های Tailwind |

افزونه‌ها را فقط از ناشرهای معتبر نصب کنید؛ هر افزونه به فایل‌های پروژهٔ شما دسترسی دارد.

## دیباگر داخلی

به‌جای پر کردن کد با `print`، روی شمارهٔ خط کلیک کنید تا **breakpoint** بگذارید و `F5` را بزنید. می‌توانید مقدار
متغیرها را ببینید، خط‌به‌خط جلو بروید و عبارت‌ها را در کنسول دیباگ ارزیابی کنید.

## همگام‌سازی

با **Settings Sync** (نماد حساب کاربری پایین نوار کناری)، تنظیمات، میانبرها و افزونه‌ها روی همهٔ کامپیوترهای شما
یکسان می‌شود.
""",
    ),
    dict(
        title="React برای شروع: کامپوننت، props و state",
        category="web", type="tutorial", tags=["React", "JavaScript", "Frontend"], label="REACT", photo="1603302576837-37561b2e2302",
        excerpt="React رابط کاربری را از قطعه‌های کوچک و قابل‌استفادهٔ مجدد می‌سازد. سه مفهوم پایه را با ساخت یک فهرست "
                "کارها یاد بگیرید.",
        body=r"""## ساخت پروژه

```bash
npm create vite@latest todo-app -- --template react
cd todo-app && npm install && npm run dev
```

## کامپوننت

کامپوننت تابعی است که **JSX** (ترکیبی شبیه HTML درون جاوااسکریپت) برمی‌گرداند:

```jsx
function Greeting() {
  return <h1>سلام دنیا!</h1>;
}
```

نام کامپوننت باید با **حرف بزرگ** شروع شود.

## props: ورودی کامپوننت

```jsx
function Greeting({ name }) {
  return <h1>سلام {name}!</h1>;
}

<Greeting name="سارا" />
```

props فقط‌خواندنی‌اند؛ کامپوننت نباید props خودش را تغییر دهد.

## state: حافظهٔ کامپوننت

```jsx
import { useState } from "react";

function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count} بار کلیک شد</button>;
}
```

با هر فراخوانی `setCount`، React کامپوننت را دوباره رندر می‌کند.

## پروژه: فهرست کارها

```jsx
import { useState } from "react";

function TodoItem({ todo, onToggle }) {
  return (
    <li onClick={() => onToggle(todo.id)} style={{ textDecoration: todo.done ? "line-through" : "none" }}>
      {todo.title}
    </li>
  );
}

export default function App() {
  const [todos, setTodos] = useState([]);
  const [text, setText] = useState("");

  function addTodo(event) {
    event.preventDefault();
    if (!text.trim()) return;
    setTodos([...todos, { id: crypto.randomUUID(), title: text, done: false }]);
    setText("");
  }

  function toggle(id) {
    setTodos(todos.map((t) => (t.id === id ? { ...t, done: !t.done } : t)));
  }

  return (
    <main dir="rtl">
      <form onSubmit={addTodo}>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="کار جدید..." />
        <button>افزودن</button>
      </form>
      <ul>
        {todos.map((todo) => (
          <TodoItem key={todo.id} todo={todo} onToggle={toggle} />
        ))}
      </ul>
    </main>
  );
}
```

## سه قاعدهٔ مهم

1. **state را مستقیم تغییر ندهید.** به‌جای `todos.push(...)` آرایهٔ جدید بسازید؛ وگرنه React تغییر را نمی‌بیند.
2. **هر عنصر فهرست `key` یکتا و پایدار بخواهد.** از اندیس آرایه به‌عنوان key استفاده نکنید، چون با حذف و جابه‌جایی
   عوض می‌شود.
3. **داده از بالا به پایین جریان دارد.** state در والد نگه داشته می‌شود و فرزند با تابعی که از props گرفته (مثل
   `onToggle`) تغییر را درخواست می‌کند.

## useEffect: ارتباط با دنیای بیرون

```jsx
import { useEffect, useState } from "react";

function Articles() {
  const [articles, setArticles] = useState([]);
  useEffect(() => {
    fetch("/api/articles/")
      .then((r) => r.json())
      .then(setArticles);
  }, []);   // آرایهٔ خالی: فقط یک بار بعد از اولین رندر
  return <ul>{articles.map((a) => <li key={a.id}>{a.title}</li>)}</ul>;
}
```

## قدم بعدی

مسیریابی با React Router، مدیریت دادهٔ سرور با TanStack Query، و برای سئو و رندر سمت سرور، فریم‌ورک‌هایی مثل
Next.js.
""",
    ),
    dict(
        title="Kotlin برای شروع برنامه‌نویسی اندروید",
        category="mobile", type="tutorial", tags=["Kotlin", "Android", "Mobile"], label="KOTLIN", photo="1601972599720-36938d4ecd31",
        excerpt="Kotlin زبان پیشنهادی گوگل برای اندروید است: کوتاه‌تر از جاوا و امن‌تر در برابر NullPointerException. "
                "مفاهیم پایه را با مثال یاد بگیرید.",
        body=r"""## چرا Kotlin؟

Kotlin را شرکت JetBrains ساخت و گوگل در سال ۲۰۱۹ اعلام کرد توسعهٔ اندروید را «Kotlin-first» پیش می‌برد. این زبان
با جاوا کاملاً سازگار است و روی JVM اجرا می‌شود.

برای تمرین بدون نصب، از **Kotlin Playground** در سایت رسمی kotlinlang.org استفاده کنید؛ برای اندروید، **Android
Studio** را نصب کنید.

## متغیرها

```kotlin
val name = "Sara"      // تغییرناپذیر (مثل final)
var score = 10         // تغییرپذیر
score += 5
val pi: Double = 3.14  // تعیین صریح نوع
```

قاعده: پیش‌فرض را `val` بگذارید و فقط وقتی واقعاً لازم است `var` استفاده کنید.

## امنیت در برابر null

```kotlin
var city: String = "Tehran"
// city = null           // خطای کامپایل!

var nickname: String? = null   // ? یعنی می‌تواند null باشد
println(nickname?.length)       // اگر null بود، null برمی‌گرداند
println(nickname?.length ?: 0)  // عملگر Elvis: مقدار پیش‌فرض
```

بیشتر خطاهای NullPointerException جاوا در Kotlin همان زمان کامپایل گرفته می‌شوند.

## تابع

```kotlin
fun greet(name: String, greeting: String = "سلام"): String {
    return "$greeting $name!"
}

fun square(x: Int) = x * x   // تابع تک‌عبارتی

greet("Reza")
greet(name = "Mina", greeting = "درود")
```

## when: switch قدرتمند

```kotlin
fun describe(code: Int) = when (code) {
    200 -> "OK"
    404 -> "Not Found"
    in 500..599 -> "Server Error"
    else -> "Unknown"
}
```

## data class

```kotlin
data class User(val id: Int, val name: String, val email: String)

val u = User(1, "Sara", "sara@example.com")
val renamed = u.copy(name = "Sara A.")
println(u)   // User(id=1, name=Sara, email=sara@example.com)
```

`equals`، `hashCode`، `toString` و `copy` به‌طور خودکار ساخته می‌شوند.

## مجموعه‌ها

```kotlin
val numbers = listOf(5, 2, 8, 1)
val evens = numbers.filter { it % 2 == 0 }
val doubled = numbers.map { it * 2 }
val total = numbers.sum()

val ages = mapOf("Sara" to 28, "Reza" to 31)
```

`it` نام پیش‌فرض تنها پارامتر یک lambda است.

## تابع الحاقی (Extension)

```kotlin
fun String.isValidEmail() = contains("@") && contains(".")

"me@example.com".isValidEmail()   // true
```

## قدم بعدی

بعد از این مفاهیم، سراغ **Jetpack Compose** برای ساخت رابط کاربری و **Coroutines** برای کارهای ناهم‌زمان مثل
درخواست شبکه بروید.
""",
    ),
    dict(
        title="SwiftUI برای شروع: ساخت اولین اپ iOS",
        category="mobile", type="tutorial", tags=["SwiftUI", "iOS", "Swift"], label="SWIFTUI", photo="1556656793-08538906a9f8",
        excerpt="SwiftUI رابط کاربری اپ‌های اپل را به روش اعلانی و با کد کم می‌سازد. View، modifier و State را با یک اپ "
                "شمارنده و فهرست یاد بگیرید.",
        body=r"""## پیش‌نیاز

برای توسعهٔ iOS به یک مک و **Xcode** نیاز دارید. یک پروژهٔ جدید «App» بسازید و Interface را روی SwiftUI بگذارید.
پیش‌نمایش زنده (Preview) تغییرات را بلافاصله نشان می‌دهد.

## View

هر بخش از رابط کاربری یک `View` است:

```swift
import SwiftUI

struct ContentView: View {
    var body: some View {
        Text("سلام دنیا!")
            .font(.largeTitle)
            .foregroundStyle(.blue)
            .padding()
    }
}
```

متدهایی مثل `.font` و `.padding` را **modifier** می‌گویند. ترتیب آن‌ها مهم است: `padding` قبل از `background` با
`padding` بعد از آن نتیجهٔ متفاوتی دارد.

## چیدمان

```swift
VStack(spacing: 16) {          // عمودی
    HStack {                   // افقی
        Image(systemName: "star.fill")
        Text("علاقه‌مندی‌ها")
    }
    Spacer()
}
```

`ZStack` هم عناصر را روی هم قرار می‌دهد.

## State: داده‌ای که رابط کاربری را به‌روز می‌کند

```swift
struct CounterView: View {
    @State private var count = 0

    var body: some View {
        VStack {
            Text("\(count)")
                .font(.system(size: 64, weight: .bold))
            Button("افزایش") {
                count += 1
            }
            .buttonStyle(.borderedProminent)
        }
    }
}
```

با تغییر `count`، SwiftUI خودش بخش‌های وابسته را دوباره رسم می‌کند.

## فهرست و ناوبری

```swift
struct Article: Identifiable {
    let id = UUID()
    let title: String
}

struct ArticlesView: View {
    let articles = [Article(title: "آموزش Git"), Article(title: "مقدمه‌ای بر SQL")]

    var body: some View {
        NavigationStack {
            List(articles) { article in
                NavigationLink(article.title) {
                    Text(article.title).font(.title)
                }
            }
            .navigationTitle("مقاله‌ها")
        }
    }
}
```

## ورودی کاربر و Binding

```swift
@State private var name = ""

TextField("نام شما", text: $name)
Text("سلام \(name)")
```

علامت `$` یک **Binding** می‌سازد: TextField مستقیماً همان State را می‌خواند و تغییر می‌دهد.

## راست‌به‌چپ

SwiftUI وقتی زبان دستگاه فارسی باشد، چیدمان را خودکار راست‌به‌چپ می‌کند. برای آزمایش در پیش‌نمایش:

```swift
#Preview {
    ContentView().environment(\.layoutDirection, .rightToLeft)
}
```

## قدم بعدی

گرفتن داده از API با `async/await` و `URLSession`، و ذخیرهٔ محلی داده با **SwiftData**.
""",
    ),
    dict(
        title="ساخت اولین بازی دوبعدی با Godot و GDScript",
        category="gaming", type="tutorial", tags=["Godot", "Game Development", "GDScript"], label="GODOT 2D",
        photo="1552820728-8b83bb6b773f",
        excerpt="یک شخصیت قابل کنترل، سکه‌هایی برای جمع کردن و یک امتیاز؛ قدم‌به‌قدم اولین بازی دوبعدی خود را در موتور "
                "متن‌باز Godot 4 بسازید.",
        body=r"""## نصب

Godot را از سایت رسمی godotengine.org دانلود کنید. نسخهٔ استاندارد فقط یک فایل اجرایی است و نصب خاصی نمی‌خواهد.
این آموزش برای **Godot 4** نوشته شده است.

## مفاهیم پایه

- **Node:** کوچک‌ترین جزء؛ هر Node یک کار انجام می‌دهد (نمایش تصویر، تشخیص برخورد، پخش صدا).
- **Scene:** درختی از Nodeها که قابل ذخیره و استفادهٔ دوباره است؛ مثلاً «بازیکن» یا «سکه».
- **Script:** رفتار یک Node، معمولاً با زبان GDScript که شبیه پایتون است.

## ۱. صحنهٔ بازیکن

یک صحنهٔ جدید با این ساختار بسازید:

```text
Player (CharacterBody2D)
├── Sprite2D           ← تصویر شخصیت
└── CollisionShape2D   ← شکل برخورد (مثلاً مستطیل)
```

اسکریپت `player.gd`:

```gdscript
extends CharacterBody2D

const SPEED = 300.0

func _physics_process(delta):
    var direction = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    velocity = direction * SPEED
    move_and_slide()
```

`ui_left` و بقیه، کلیدهای جهت‌نمای پیش‌فرض هستند. `move_and_slide()` حرکت را با در نظر گرفتن برخوردها انجام می‌دهد.

## ۲. صحنهٔ سکه

```text
Coin (Area2D)
├── Sprite2D
└── CollisionShape2D
```

اسکریپت `coin.gd`:

```gdscript
extends Area2D

signal collected

func _ready():
    body_entered.connect(_on_body_entered)

func _on_body_entered(body):
    if body.name == "Player":
        collected.emit()
        queue_free()
```

**Signal** روش Godot برای خبر دادن یک اتفاق به بقیهٔ بازی است؛ سکه نمی‌داند امتیاز کجا نگه داشته می‌شود.

## ۳. صحنهٔ اصلی

```text
Main (Node2D)
├── Player
├── Coins (Node2D)  ← چند نمونه از صحنهٔ Coin
└── ScoreLabel (Label)
```

اسکریپت `main.gd`:

```gdscript
extends Node2D

var score = 0

func _ready():
    for coin in $Coins.get_children():
        coin.collected.connect(_on_coin_collected)
    _update_label()

func _on_coin_collected():
    score += 1
    _update_label()
    if $Coins.get_child_count() <= 1:
        $ScoreLabel.text = "بردی! امتیاز: %d" % score

func _update_label():
    $ScoreLabel.text = "امتیاز: %d" % score
```

(شرط `<= 1` به این خاطر است که سکهٔ آخر در همان فریم هنوز کاملاً حذف نشده است.)

برای نمایش درست متن فارسی در Label، یک فونت فارسی مثل وزیرمتن به پروژه اضافه و در تنظیمات Label انتخاب کنید.

## ۴. اجرا و خروجی

`F5` بازی را اجرا می‌کند. از منوی **Project → Export** می‌توانید برای ویندوز، لینوکس، اندروید یا وب خروجی بگیرید.

## ایده‌هایی برای ادامه

- دشمنی که به سمت بازیکن حرکت می‌کند
- زمان‌سنج معکوس با Node از نوع `Timer`
- صدا هنگام جمع کردن سکه با `AudioStreamPlayer2D`
""",
    ),
    dict(
        title="تحلیل ترافیک شبکه با Wireshark: آموزش کاربردی",
        category="security", type="tutorial", tags=["Wireshark", "Network", "Troubleshooting"], label="WIRESHARK",
        photo="1489389944381-3471b5b30f04",
        excerpt="وقتی برنامه «به سرور وصل نمی‌شود»، Wireshark نشان می‌دهد دقیقاً چه بسته‌هایی رفت و آمد. ضبط ترافیک، "
                "فیلترها و عیب‌یابی رایج‌ترین مشکلات.",
        body=r"""## پیش از شروع

ترافیک را فقط روی **شبکه و دستگاه‌های خودتان** یا با مجوز صریح مالک شبکه ضبط کنید. شنود ترافیک دیگران در بیشتر
کشورها غیرقانونی است و ترافیک ضبط‌شده ممکن است شامل اطلاعات حساس باشد؛ از آن مثل یک فایل محرمانه محافظت کنید.

## نصب

Wireshark را از سایت رسمی wireshark.org یا مخزن سیستم‌عامل نصب کنید. در لینوکس:

```bash
sudo apt install wireshark
sudo usermod -aG wireshark $USER   # ضبط بدون sudo؛ بعد دوباره وارد شوید
```

## ضبط ترافیک

1. کارت شبکهٔ فعال (مثلاً Wi-Fi) را انتخاب کنید.
2. دکمهٔ آبی‌رنگ شروع (به شکل بالهٔ کوسه) را بزنید تا ضبط آغاز شود.
3. کاری را که می‌خواهید بررسی کنید انجام دهید و ضبط را متوقف کنید.

## فیلتر ضبط در برابر فیلتر نمایش

| | Capture Filter | Display Filter |
|---|---|---|
| زمان اعمال | قبل از ضبط | بعد از ضبط |
| زبان | BPF | زبان خود Wireshark |
| مثال | `port 53` | `dns` |

## فیلترهای نمایش پرکاربرد

```text
ip.addr == 192.168.1.10          ترافیک یک دستگاه
tcp.port == 443                  ترافیک HTTPS
dns                              فقط DNS
http.request                     درخواست‌های HTTP رمزنشده
tcp.flags.syn == 1 && tcp.flags.ack == 0   شروع اتصال‌های TCP
tcp.analysis.retransmission      بسته‌های ارسال‌شده دوباره
!(arp || mdns)                   حذف ترافیک شلوغ و بی‌ربط
```

## سناریوهای عیب‌یابی

### سایت باز نمی‌شود

1. فیلتر `dns`: آیا پاسخ DNS آمد؟ اگر پاسخ `No such name` بود، مشکل از نام دامنه است.
2. فیلتر `tcp.port == 443`: آیا بستهٔ SYN فرستاده شد و SYN-ACK برگشت؟
   - پاسخی نیامد: فایروال یا مسیر شبکه.
   - **RST** برگشت: سرور در دسترس است، اما روی آن پورت سرویسی گوش نمی‌دهد.

### اتصال کند است

فیلتر `tcp.analysis.flags` بسته‌های گم‌شده، تکراری و مشکلات پنجرهٔ TCP را نشان می‌دهد. از منوی **Statistics → I/O
Graphs** هم الگوی ترافیک در طول زمان را ببینید.

## دنبال کردن یک گفت‌وگو

روی یک بسته راست‌کلیک کنید و **Follow → TCP Stream** را بزنید تا کل گفت‌وگوی آن اتصال به ترتیب نمایش داده شود.

## ترافیک HTTPS

محتوای HTTPS رمزشده است و فقط فراداده‌هایی مثل IP، پورت و نام سرور (SNI) دیده می‌شود. برای دیباگ برنامهٔ
**خودتان** در مرورگر، می‌توانید کلیدهای نشست را با متغیر محیطی `SSLKEYLOGFILE` ذخیره و در تنظیمات TLS وایرشارک
وارد کنید.

## ضبط روی سرور بدون رابط گرافیکی

```bash
sudo tcpdump -i eth0 -w capture.pcap port 443
```

فایل `capture.pcap` را به کامپیوتر خود منتقل و در Wireshark باز کنید.
""",
    ),
    dict(
        title="Nmap برای مدیران شبکه: شناخت دستگاه‌ها و سرویس‌های شبکهٔ خودتان",
        category="security", type="tutorial", tags=["Nmap", "Network Security", "Linux"], label="NMAP", photo="1504384764586-bb4cdc1707b0",
        excerpt="چه دستگاه‌هایی به شبکهٔ شما وصل‌اند و چه پورت‌هایی باز گذاشته‌اند؟ با Nmap از شبکهٔ خودتان فهرست تهیه "
                "کنید و سرویس‌های ناخواسته را پیدا کنید.",
        body=r"""## هشدار قانونی

اسکن شبکه یا سروری که مالکش نیستید یا مجوز کتبی برای آزمودنش ندارید، می‌تواند **غیرقانونی** باشد و حتی اسکن
مجاز هم ممکن است سیستم‌های حساس را مختل کند. این آموزش برای بررسی **شبکه و سرورهای خودتان** است.

## نصب

```bash
sudo apt install nmap      # دبیان و اوبونتو
brew install nmap          # macOS
```

در ویندوز، نسخهٔ نصبی را از سایت رسمی nmap.org دانلود کنید.

## ۱. چه دستگاه‌هایی روشن‌اند؟

```bash
nmap -sn 192.168.1.0/24
```

`-sn` فقط دستگاه‌های فعال را پیدا می‌کند، بدون اسکن پورت. محدودهٔ شبکهٔ خود را با `ip a` (لینوکس) یا `ipconfig`
(ویندوز) پیدا کنید.

## ۲. چه پورت‌هایی باز است؟

```bash
nmap 192.168.1.20                 # ۱۰۰۰ پورت رایج
nmap -p 22,80,443 192.168.1.20    # پورت‌های مشخص
nmap -p- 192.168.1.20             # همهٔ ۶۵۵۳۵ پورت TCP (کندتر)
```

| وضعیت | معنی |
|---|---|
| open | سرویسی روی این پورت گوش می‌دهد |
| closed | دستگاه پاسخ داد اما سرویسی نیست |
| filtered | فایروال جلوی پاسخ را گرفته |

## ۳. چه سرویس و نسخه‌ای؟

```bash
nmap -sV 192.168.1.20
```

```text
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 9.6
80/tcp   open  http    nginx 1.24.0
3306/tcp open  mysql   MySQL 8.0
```

در این مثال، اگر قرار نیست MySQL از شبکه در دسترس باشد، پورت 3306 یک **یافتهٔ امنیتی** است.

## ۴. خروجی برای مقایسه

```bash
nmap -sV -oA scan-$(date +%F) 192.168.1.0/24
```

`-oA` نتیجه را در سه قالب (معمولی، XML و grepable) ذخیره می‌کند. با تکرار دوره‌ای و مقایسهٔ نتیجه‌ها، دستگاه یا
پورت جدیدی را که بی‌خبر اضافه شده پیدا کنید. ابزار `ndiff` همراه Nmap دو اسکن XML را مقایسه می‌کند.

## ۵. سرور خودتان از بیرون

از یک سرور یا اینترنت دیگر، **IP عمومی سرور خودتان** را اسکن کنید تا ببینید دنیا چه می‌بیند:

```bash
nmap -sV -Pn your-server.example.com
```

`-Pn` یعنی فرض کن دستگاه روشن است، حتی اگر به ping پاسخ ندهد.

## بعد از اسکن چه کنیم؟

1. هر پورت باز را توضیح دهید: کدام سرویس است و چرا باید باز باشد؟
2. سرویس‌های غیرضروری را خاموش کنید.
3. سرویس‌هایی مثل دیتابیس را طوری تنظیم کنید که فقط روی `127.0.0.1` یا شبکهٔ داخلی در دسترس باشند.
4. با فایروال (مثلاً `ufw`) فقط پورت‌های لازم را باز بگذارید.
5. نسخه‌های قدیمی را به‌روز کنید.

```bash
sudo ufw default deny incoming
sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw enable
```
""",
    ),
    dict(
        title="پشتیبان‌گیری و بازیابی PostgreSQL با pg_dump",
        category="database", type="tutorial", tags=["PostgreSQL", "Backup", "Database"], label="PG_DUMP",
        photo="1580894908361-967195033215",
        excerpt="پشتیبانی که بازیابی‌اش را امتحان نکرده‌اید، پشتیبان نیست. روش درست گرفتن، خودکار کردن و بازگرداندن "
                "نسخهٔ پشتیبان PostgreSQL.",
        body=r"""## ابزارها

| ابزار | کاربرد |
|---|---|
| `pg_dump` | پشتیبان از **یک** دیتابیس |
| `pg_dumpall` | همهٔ دیتابیس‌ها به‌علاوهٔ نقش‌ها (کاربران) |
| `pg_restore` | بازیابی پشتیبان‌های غیرمتنی |
| `psql` | اجرای پشتیبان‌های متنی SQL |

`pg_dump` حتی وقتی دیتابیس در حال استفاده است، یک **تصویر سازگار** از آن می‌گیرد و جلوی خواندن و نوشتن کاربران را
نمی‌گیرد.

## قالب‌ها

```bash
# متن SQL؛ خوانا، اما بازیابی انتخابی ندارد
pg_dump -d mydb -f mydb.sql

# قالب سفارشی (پیشنهادی)؛ فشرده، با امکان بازیابی انتخابی و موازی
pg_dump -Fc -d mydb -f mydb.dump
```

اتصال به سرور دیگر:

```bash
pg_dump -h db.example.com -U backup_user -Fc -d mydb -f mydb.dump
```

رمز را در فایل `~/.pgpass` با مجوز `600` بگذارید، نه در خط فرمان:

```text
db.example.com:5432:mydb:backup_user:SECRET
```

## بازیابی

```bash
createdb mydb_restored
pg_restore -d mydb_restored --no-owner -j 4 mydb.dump
```

| گزینه | کاربرد |
|---|---|
| `-j 4` | بازیابی موازی با ۴ پردازه |
| `--no-owner` | وقتی کاربر مالک در سرور جدید وجود ندارد |
| `-t articles` | فقط یک جدول |
| `--clean --if-exists` | حذف اشیای موجود قبل از بازیابی |

فهرست محتوای یک پشتیبان:

```bash
pg_restore -l mydb.dump | head
```

## نقش‌ها و کاربران

`pg_dump` کاربران را ذخیره نمی‌کند. آن‌ها را جداگانه پشتیبان بگیرید:

```bash
pg_dumpall --globals-only -f globals.sql
```

## اسکریپت خودکار روزانه

```bash
#!/usr/bin/env bash
set -euo pipefail

dir=/var/backups/postgres
mkdir -p "$dir"
file="$dir/mydb-$(date +%F).dump"

pg_dump -Fc -d mydb -f "$file"
pg_restore -l "$file" > /dev/null   # بررسی سالم بودن فایل
find "$dir" -name 'mydb-*.dump' -mtime +14 -delete
```

و در crontab کاربر `postgres`:

```text
30 2 * * * /usr/local/bin/pg-backup.sh >> /var/log/pg-backup.log 2>&1
```

## قاعدهٔ ۳-۲-۱

- **۳** نسخه از داده
- روی **۲** نوع رسانهٔ متفاوت
- **۱** نسخه بیرون از محل (مثلاً فضای ذخیره‌سازی ابری با رمزنگاری)

## آزمون بازیابی

هر چند وقت یک بار، پشتیبان را روی یک سرور آزمایشی بازیابی کنید و بررسی کنید برنامه با آن بالا می‌آید. زمان
بازیابی را هم اندازه بگیرید؛ این عدد نشان می‌دهد در روز بحران چقدر طول می‌کشد تا سرویس برگردد.

## فراتر از pg_dump

برای دیتابیس‌های بزرگ یا وقتی نمی‌خواهید بیش از چند دقیقه داده از دست بدهید، به پشتیبان‌گیری فیزیکی و **بازیابی
تا یک لحظهٔ مشخص (PITR)** با ابزارهایی مثل `pg_basebackup`، pgBackRest یا Barman نگاه کنید.
""",
    ),
    dict(
        title="کش در جنگو: سریع‌تر کردن سایت با Redis",
        category="web", type="tutorial", tags=["Django", "Cache", "Redis"], label="DJANGO CACHE", photo="1614624532983-4ce03382d63d",
        excerpt="بیشتر صفحه‌ها برای همهٔ بازدیدکنندگان یکسان‌اند؛ چرا هر بار از اول ساخته شوند؟ سطح‌های مختلف کش در جنگو "
                "و نکته‌هایی برای اینکه دادهٔ کهنه نشان ندهید.",
        body=r"""## راه‌اندازی Redis به‌عنوان کش

از جنگو ۴ به بعد، پشتیبانی از Redis داخل خود جنگوست:

```bash
pip install redis
```

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "TIMEOUT": 300,
    }
}
```

برای توسعه بدون Redis، `LocMemCache` کافی است.

## سطح ۱: کش کل صفحه

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)
def article_list(request):
    ...
```

ساده و مؤثر، اما مراقب باشید: صفحه‌هایی که برای هر کاربر متفاوت‌اند (نام کاربر در هدر، سبد خرید) را این‌گونه کش
نکنید، وگرنه کاربران صفحهٔ هم را می‌بینند.

## سطح ۲: کش بخشی از قالب

```django
{% load cache %}
{% cache 600 sidebar_popular %}
  {% for article in popular_articles %}...{% endfor %}
{% endcache %}
```

کش جداگانه برای هر زبان یا کاربر:

```django
{% cache 600 sidebar request.LANGUAGE_CODE %}
```

## سطح ۳: کش داده (API پایین‌دستی)

```python
from django.core.cache import cache

def get_popular_articles():
    return cache.get_or_set(
        "popular_articles",
        lambda: list(Article.objects.published().order_by("-views")[:10]),
        timeout=600,
    )
```

به `list(...)` دقت کنید: QuerySet تنبل است و باید پیش از ذخیره در کش، اجرا شود.

## باطل کردن کش

> در علوم کامپیوتر فقط دو کار سخت وجود دارد: باطل کردن کش و نام‌گذاری.

### راه ۱: حذف هنگام تغییر

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Article)
def clear_article_cache(sender, instance, **kwargs):
    cache.delete("popular_articles")
```

### راه ۲: نسخه در کلید

به‌جای پیدا کردن و حذف همهٔ کلیدها، یک «شمارهٔ نسخه» نگه دارید و آن را در همهٔ کلیدها بگذارید. با هر تغییر محتوا،
نسخه را یکی بالا ببرید تا همهٔ کلیدهای قدیمی خودبه‌خود بی‌استفاده شوند:

```python
version = cache.get_or_set("content_version", 1)
key = f"home:{version}"
...
cache.incr("content_version")   # بعد از هر تغییر محتوا
```

همین مجله از روشی شبیه این استفاده می‌کند.

## Cache Stampede

وقتی یک کلید پرطرفدار منقضی می‌شود، صدها درخواست هم‌زمان سراغ دیتابیس می‌روند. راه‌حل‌ها: زمان انقضای کمی تصادفی،
یا به‌روزرسانی کش در پس‌زمینه پیش از انقضا.

## اندازه‌گیری، نه حدس

قبل از کش کردن، با django-debug-toolbar ببینید کجا کند است. کش اشتباه پیچیدگی اضافه می‌کند و مشکل اصلی، مثل یک
ایندکس فراموش‌شده یا مشکل N+1، را پنهان می‌کند.
""",
    ),
]
