"""Fourth batch, part three: tutorials 1–15."""

FRESH_TUTORIALS = [
    dict(
        title="آموزش Git از صفر: init، commit، branch و merge",
        category="tutorials", type="tutorial", tags=["Git", "Version Control", "Tutorial"], label="GIT", photo="1556075798-4825dfaaf498",
        excerpt="اگر هنوز پروژه‌هایتان را با نام‌هایی مثل «نهایی-۲-واقعا-نهایی» نگه می‌دارید، وقت یادگیری Git است. "
                "قدم‌به‌قدم از اولین commit تا ادغام شاخه‌ها.",
        body=r"""## نصب و تنظیم اولیه

```bash
git --version
git config --global user.name "Sara Ahmadi"
git config --global user.email "sara@example.com"
git config --global init.defaultBranch main
```

## ۱. ساخت مخزن

```bash
mkdir my-project && cd my-project
git init
```

## ۲. سه ناحیهٔ Git

| ناحیه | توضیح |
|---|---|
| Working Directory | فایل‌هایی که ویرایش می‌کنید |
| Staging Area | تغییراتی که برای commit بعدی انتخاب کرده‌اید |
| Repository | تاریخچهٔ commitها |

## ۳. اولین commit

```bash
echo "# My Project" > README.md
git status            # فایل جدید را می‌بیند
git add README.md     # به staging می‌برد
git commit -m "Add README"
git log --oneline     # تاریخچه
```

پیام commit را کوتاه و گویا بنویسید و بگویید **چه** تغییری داده‌اید: «Fix login redirect» بهتر از «update» است.

## ۴. دیدن تغییرات

```bash
git diff              # تغییرات stage نشده
git diff --staged     # تغییرات stage شده
```

## ۵. شاخه (Branch)

شاخه به شما اجازه می‌دهد روی یک ویژگی کار کنید، بدون اینکه شاخهٔ اصلی خراب شود:

```bash
git switch -c feature/login   # ساخت شاخه و رفتن به آن
# ... ویرایش و commit ...
git switch main               # برگشت به شاخهٔ اصلی
```

## ۶. ادغام (Merge)

```bash
git switch main
git merge feature/login
git branch -d feature/login   # حذف شاخهٔ ادغام‌شده
```

### اگر تعارض (Conflict) پیش آمد

Git بخش‌های متعارض را این‌طور علامت می‌زند:

```text
<<<<<<< HEAD
title = "Home"
=======
title = "Main page"
>>>>>>> feature/login
```

نسخهٔ درست را نگه دارید، علامت‌ها را پاک کنید، سپس `git add` و `git commit` بزنید.

## ۷. اتصال به GitHub

```bash
git remote add origin https://github.com/USER/my-project.git
git push -u origin main
git pull              # گرفتن تغییرات دیگران
```

## ۸. فایل‌هایی که نباید commit شوند

یک فایل `.gitignore` بسازید:

```text
.venv/
__pycache__/
.env
node_modules/
```

فایل `.env` که رمزها و کلیدها در آن است، **هرگز** نباید وارد مخزن شود.

## دستورهای نجات

| موقعیت | دستور |
|---|---|
| لغو تغییرات یک فایل | `git restore file.py` |
| خارج کردن از staging | `git restore --staged file.py` |
| تغییر پیام آخرین commit (قبل از push) | `git commit --amend` |
| کنار گذاشتن موقت تغییرات | `git stash` و بعد `git stash pop` |
""",
    ),
    dict(
        title="محیط مجازی پایتون: venv و pip را درست به کار ببرید",
        category="tutorials", type="tutorial", tags=["Python", "venv", "pip"], label="VENV", photo="1649180556628-9ba704115795",
        excerpt="نصب همهٔ کتابخانه‌ها روی پایتون سیستم، دیر یا زود پروژه‌ها را به جان هم می‌اندازد. با محیط مجازی، هر "
                "پروژه وابستگی‌های خودش را دارد.",
        body=r"""## مشکل

پروژهٔ A به Django 4.2 نیاز دارد و پروژهٔ B به Django 5.2. اگر هر دو روی پایتون سیستم نصب شوند، یکی خراب می‌شود.
**محیط مجازی** یک پوشهٔ مستقل با مفسر و کتابخانه‌های جداگانه برای هر پروژه است.

## ساخت محیط

```bash
cd my-project
python3 -m venv .venv
```

## فعال‌سازی

| سیستم | دستور |
|---|---|
| لینوکس و macOS | `source .venv/bin/activate` |
| ویندوز (PowerShell) | `.venv\Scripts\Activate.ps1` |
| ویندوز (cmd) | `.venv\Scripts\activate.bat` |

بعد از فعال‌سازی، نام محیط کنار خط فرمان ظاهر می‌شود و `python` و `pip` به نسخه‌های داخل `.venv` اشاره می‌کنند:

```bash
which python      # .../my-project/.venv/bin/python
deactivate        # خروج از محیط
```

## نصب کتابخانه‌ها

```bash
python -m pip install --upgrade pip
pip install django requests
pip list
```

استفاده از `python -m pip` به‌جای `pip` خالی تضمین می‌کند pip همان پایتونی را هدف بگیرد که انتظار دارید.

## ثبت وابستگی‌ها

```bash
pip freeze > requirements.txt
```

و روی سیستم دیگر یا سرور:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### نسخه‌ها را مشخص کنید

```text
Django>=5.2,<5.3
requests==2.32.3
```

بدون محدودیت نسخه، نصب چند ماه بعد ممکن است نسخهٔ جدیدی بیاورد که با کد شما سازگار نیست.

## نکته‌ها

- پوشهٔ `.venv` را به `.gitignore` اضافه کنید؛ فقط `requirements.txt` در مخزن قرار می‌گیرد.
- هرگز با `sudo pip install` روی پایتون سیستم نصب نکنید؛ ممکن است ابزارهای سیستم‌عامل را خراب کند.
- اگر محیط خراب شد، نگران نباشید: پوشه را پاک کنید و از روی `requirements.txt` دوباره بسازید.

## ابزارهای جدیدتر

**uv** ابزاری بسیار سریع است که ساخت محیط و نصب بسته‌ها را یکجا انجام می‌دهد:

```bash
uv venv
uv pip install -r requirements.txt
```

ابزارهایی مثل Poetry و uv فایل **lock** هم می‌سازند تا نسخهٔ دقیق همهٔ وابستگی‌های غیرمستقیم ثبت شود.
""",
    ),
    dict(
        title="SQL برای شروع: SELECT، WHERE، JOIN و GROUP BY",
        category="database", type="tutorial", tags=["SQL", "Database", "PostgreSQL"], label="SQL", photo="1627398242454-45a1465c2479",
        excerpt="SQL زبان مشترک تقریباً همهٔ پایگاه‌داده‌های رابطه‌ای است. با یک مثال فروشگاهی، پرکاربردترین دستورها "
                "را در کمتر از نیم ساعت یاد بگیرید.",
        body=r"""## دادهٔ نمونه

```sql
CREATE TABLE customers (id INT PRIMARY KEY, name TEXT, city TEXT);
CREATE TABLE orders (
    id INT PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    amount NUMERIC,
    created_at DATE
);

INSERT INTO customers VALUES (1, 'Sara', 'Tehran'), (2, 'Reza', 'Shiraz'), (3, 'Mina', 'Tehran');
INSERT INTO orders VALUES
    (1, 1, 250, '2026-09-01'), (2, 1, 120, '2026-09-15'),
    (3, 2, 980, '2026-09-20');
```

## SELECT و WHERE

```sql
SELECT name, city FROM customers;

SELECT * FROM orders
WHERE amount > 200 AND created_at >= '2026-09-10';
```

## مرتب‌سازی و محدود کردن

```sql
SELECT * FROM orders ORDER BY amount DESC LIMIT 2;
```

## الگو و فهرست

```sql
SELECT * FROM customers WHERE name LIKE 'S%';
SELECT * FROM customers WHERE city IN ('Tehran', 'Isfahan');
SELECT * FROM orders WHERE amount BETWEEN 100 AND 500;
```

## JOIN: ترکیب جدول‌ها

```sql
SELECT c.name, o.amount
FROM orders AS o
JOIN customers AS c ON c.id = o.customer_id;
```

| نوع | نتیجه |
|---|---|
| `INNER JOIN` | فقط ردیف‌هایی که در هر دو جدول جفت دارند |
| `LEFT JOIN` | همهٔ ردیف‌های جدول چپ؛ اگر جفت نبود، NULL |
| `FULL JOIN` | همهٔ ردیف‌های هر دو جدول |

مثلاً برای دیدن مشتری‌هایی که **هیچ** سفارشی نداده‌اند:

```sql
SELECT c.name
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.id
WHERE o.id IS NULL;
```

## GROUP BY و توابع تجمیعی

```sql
SELECT c.name, COUNT(o.id) AS order_count, SUM(o.amount) AS total
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.id
GROUP BY c.name
HAVING COUNT(o.id) > 0
ORDER BY total DESC;
```

- `WHERE` ردیف‌ها را **قبل** از گروه‌بندی فیلتر می‌کند.
- `HAVING` گروه‌ها را **بعد** از گروه‌بندی فیلتر می‌کند.

## UPDATE و DELETE با احتیاط

```sql
UPDATE customers SET city = 'Isfahan' WHERE id = 2;
DELETE FROM orders WHERE id = 3;
```

> هرگز UPDATE یا DELETE بدون WHERE اجرا نکنید، مگر واقعاً بخواهید همهٔ ردیف‌ها تغییر کنند. قبل از اجرا، همان شرط
> را با یک SELECT امتحان کنید.

## قدم بعدی

برای تمرین، PostgreSQL یا SQLite را نصب کنید؛ SQLite حتی نصب سرور هم نمی‌خواهد و همراه پایتون وجود دارد.
""",
    ),
    dict(
        title="ORM جنگو را حرفه‌ای به کار ببرید: select_related، annotate و F",
        category="web", type="tutorial", tags=["Django", "ORM", "Performance"], label="DJANGO ORM", photo="1546900703-cf06143d1239",
        excerpt="کندی بیشتر سایت‌های جنگو به کوئری‌های اضافه برمی‌گردد، نه خود پایتون. با چند ابزار ORM، تعداد کوئری‌ها "
                "را از صدها به چند عدد برسانید.",
        body=r"""## مدل‌های نمونه

```python
class Author(models.Model):
    name = models.CharField(max_length=100)

class Article(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="articles")
    tags = models.ManyToManyField("Tag")
    views = models.PositiveIntegerField(default=0)
```

## مشکل N+1

```python
for article in Article.objects.all():
    print(article.author.name)   # برای هر مقاله یک کوئری جدا!
```

با ۱۰۰ مقاله، ۱۰۱ کوئری اجرا می‌شود.

## select_related برای ForeignKey

```python
for article in Article.objects.select_related("author"):
    print(article.author.name)   # فقط یک کوئری با JOIN
```

## prefetch_related برای ManyToMany و رابطه‌های معکوس

```python
articles = Article.objects.prefetch_related("tags")
authors = Author.objects.prefetch_related("articles")
```

این روش برای هر رابطه یک کوئری جداگانه می‌زند و نتیجه‌ها را در پایتون به هم وصل می‌کند.

## annotate: محاسبه در دیتابیس

```python
from django.db.models import Count, Sum

authors = Author.objects.annotate(
    article_count=Count("articles"),
    total_views=Sum("articles__views"),
).order_by("-total_views")
```

## F: به‌روزرسانی بدون race condition

```python
from django.db.models import F

# اشتباه: دو درخواست هم‌زمان ممکن است یکدیگر را بازنویسی کنند
article.views += 1
article.save()

# درست: افزایش مستقیم در دیتابیس
Article.objects.filter(pk=article.pk).update(views=F("views") + 1)
```

## Q: شرط‌های ترکیبی

```python
from django.db.models import Q

Article.objects.filter(Q(title__icontains="python") | Q(tags__name="Python")).distinct()
```

## فقط آنچه لازم است

```python
Article.objects.only("id", "title")           # ستون‌های محدود
Article.objects.values_list("id", flat=True)  # فقط شناسه‌ها
Article.objects.filter(author=a).exists()     # سریع‌تر از count() > 0
```

## عملیات گروهی

```python
Tag.objects.bulk_create([Tag(name=n) for n in ["AI", "Web", "Security"]])
Article.objects.filter(views=0).update(views=1)
```

## کوئری‌ها را ببینید

ابزار **django-debug-toolbar** تعداد و زمان کوئری‌های هر صفحه را نشان می‌دهد. در تست‌ها هم می‌توانید تعداد
کوئری را قفل کنید:

```python
with self.assertNumQueries(2):
    list(Article.objects.select_related("author").prefetch_related("tags"))
```
""",
    ),
    dict(
        title="ساخت API با FastAPI: از Hello World تا اعتبارسنجی داده",
        category="web", type="tutorial", tags=["FastAPI", "Python", "API"], label="FASTAPI", photo="1618477388954-7852f32655ec",
        excerpt="FastAPI با type hintهای پایتون، اعتبارسنجی و مستندات خودکار API را رایگان به شما می‌دهد. یک API کامل "
                "برای مدیریت کارها بسازید.",
        body=r"""## نصب

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install "fastapi[standard]"
```

## اولین endpoint

```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="Todo API")

@app.get("/")
def read_root():
    return {"message": "سلام!"}
```

اجرا:

```bash
fastapi dev main.py
# یا: uvicorn main:app --reload
```

حالا آدرس `http://127.0.0.1:8000/docs` را باز کنید: مستندات تعاملی Swagger به‌طور **خودکار** ساخته شده است.

## پارامترهای مسیر و کوئری

```python
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

اگر به‌جای عدد بنویسید `/items/abc`، FastAPI خودش خطای ۴۲۲ با توضیح دقیق برمی‌گرداند.

## مدل داده با Pydantic

```python
from pydantic import BaseModel, Field

class TodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False

class Todo(TodoIn):
    id: int
```

## CRUD ساده

```python
from fastapi import HTTPException

todos: dict[int, Todo] = {}
next_id = 1

@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(data: TodoIn):
    global next_id
    todo = Todo(id=next_id, **data.model_dump())
    todos[next_id] = todo
    next_id += 1
    return todo

@app.get("/todos", response_model=list[Todo])
def list_todos():
    return list(todos.values())

@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    if todo_id not in todos:
        raise HTTPException(status_code=404, detail="کار پیدا نشد")
    return todos[todo_id]

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    todos.pop(todo_id, None)
```

## تست

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_todo():
    response = client.post("/todos", json={"title": "یادگیری FastAPI"})
    assert response.status_code == 201
    assert response.json()["done"] is False
```

## FastAPI یا جنگو؟

| | FastAPI | Django + DRF |
|---|---|---|
| تمرکز | API سریع و سبک | فریم‌ورک کامل با پنل مدیریت و ORM |
| async | پشتیبانی کامل از ابتدا | پشتیبانی در حال گسترش |
| مستندات API | خودکار | با بسته‌های جانبی |

قدم بعدی: اتصال به دیتابیس با SQLAlchemy یا SQLModel و افزودن احراز هویت.
""",
    ),
    dict(
        title="Fetch و Promise در جاوااسکریپت: گرفتن داده از API",
        category="web", type="tutorial", tags=["JavaScript", "Fetch API", "Async"], label="FETCH", photo="1555949963-ff9fe0c870eb",
        excerpt="درخواست به سرور، منتظر ماندن برای پاسخ و مدیریت خطا؛ با fetch و async/await این کارها را تمیز و قابل "
                "فهم بنویسید.",
        body=r"""## Promise چیست؟

Promise نمایندهٔ نتیجه‌ای است که **هنوز آماده نیست**. سه حالت دارد: در انتظار (pending)، موفق (fulfilled) و
ناموفق (rejected).

## اولین درخواست

```javascript
fetch("https://api.example.com/articles")
  .then((response) => response.json())
  .then((data) => console.log(data))
  .catch((error) => console.error(error));
```

## همان کد با async/await

```javascript
async function loadArticles() {
  const response = await fetch("https://api.example.com/articles");
  const data = await response.json();
  return data;
}
```

## دام رایج: fetch با خطای HTTP شکست نمی‌خورد

`fetch` فقط وقتی خطا می‌دهد که **شبکه** قطع باشد. پاسخ ۴۰۴ یا ۵۰۰ از نظر fetch «موفق» است! همیشه `response.ok`
را بررسی کنید:

```javascript
async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

try {
  const articles = await getJSON("/api/articles/");
  render(articles);
} catch (error) {
  showMessage("بارگذاری مقاله‌ها ممکن نشد.");
}
```

## ارسال داده (POST)

```javascript
const response = await fetch("/api/comments/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": csrfToken,
  },
  body: JSON.stringify({ text: "مقالهٔ مفیدی بود!" }),
});
```

## چند درخواست هم‌زمان

```javascript
const [user, posts] = await Promise.all([
  getJSON("/api/me/"),
  getJSON("/api/posts/"),
]);
```

| تابع | رفتار |
|---|---|
| `Promise.all` | منتظر همه می‌ماند؛ با اولین خطا شکست می‌خورد |
| `Promise.allSettled` | منتظر همه می‌ماند و نتیجهٔ هر کدام را جداگانه می‌دهد |
| `Promise.race` | اولین نتیجه (موفق یا ناموفق) |
| `Promise.any` | اولین نتیجهٔ موفق |

## محدودیت زمانی و لغو درخواست

```javascript
const response = await fetch("/api/search/?q=django", {
  signal: AbortSignal.timeout(5000), // بعد از ۵ ثانیه لغو می‌شود
});
```

برای لغو دستی (مثلاً وقتی کاربر عبارت جست‌وجو را عوض می‌کند) از `AbortController` استفاده کنید:

```javascript
let controller;
async function search(q) {
  controller?.abort();
  controller = new AbortController();
  return getJSON(`/api/search/?q=${encodeURIComponent(q)}`, { signal: controller.signal });
}
```

(برای این کار، `getJSON` را طوری تغییر دهید که پارامتر دوم را به fetch بدهد.)
""",
    ),
    dict(
        title="شروع کار با Tailwind CSS: طراحی سریع با کلاس‌های کاربردی",
        category="web", type="tutorial", tags=["Tailwind CSS", "CSS", "Frontend"], label="TAILWIND", photo="1610986603166-f78428624e76",
        excerpt="به‌جای نوشتن CSS جداگانه برای هر جزء، ظاهر را مستقیماً با کلاس‌های کوچک در HTML بسازید. نصب، مفاهیم اصلی "
                "و ساخت یک کارت ریسپانسیو.",
        body=r"""## فلسفهٔ Tailwind

Tailwind مجموعه‌ای از **کلاس‌های کاربردی (Utility Classes)** است که هر کدام یک کار کوچک انجام می‌دهند: `p-4`
فاصلهٔ داخلی، `text-lg` اندازهٔ متن، `bg-blue-600` رنگ پس‌زمینه. در زمان build فقط کلاس‌هایی که واقعاً استفاده
کرده‌اید وارد فایل نهایی CSS می‌شوند.

## نصب (Tailwind نسخهٔ ۴)

```bash
npm install tailwindcss @tailwindcss/cli
```

فایل `src/input.css`:

```css
@import "tailwindcss";
```

ساخت CSS و نظارت بر تغییرات:

```bash
npx @tailwindcss/cli -i ./src/input.css -o ./dist/output.css --watch
```

در نسخهٔ ۴ تنظیمات اصلی با CSS انجام می‌شود و دیگر به فایل `tailwind.config.js` برای شروع نیازی نیست (پروژه‌های
قدیمی‌تر مثل همین مجله هنوز از نسخهٔ ۳ و آن فایل استفاده می‌کنند).

## یک کارت ساده

```html
<article class="max-w-sm rounded-2xl bg-white p-6 shadow-lg">
  <h2 class="text-xl font-bold text-slate-900">آموزش Tailwind</h2>
  <p class="mt-2 text-slate-600 leading-7">ساخت رابط کاربری بدون ترک HTML.</p>
  <a href="#" class="mt-4 inline-block rounded-full bg-blue-600 px-5 py-2 text-white hover:bg-blue-700">
    ادامه
  </a>
</article>
```

## ریسپانسیو با پیشوندها

Tailwind **موبایل‌اول** است: کلاس بدون پیشوند برای همهٔ اندازه‌هاست و پیشوندها از آن عرض به بالا اعمال می‌شوند.

```html
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">...</div>
```

| پیشوند | حداقل عرض |
|---|---|
| `sm:` | 640px |
| `md:` | 768px |
| `lg:` | 1024px |
| `xl:` | 1280px |

## حالت‌ها

```html
<button class="bg-slate-200 hover:bg-slate-300 focus:ring-2 disabled:opacity-50 dark:bg-slate-700">
```

## راست‌به‌چپ

برای سایت فارسی، به‌جای `ml-4` و `mr-4` از کلاس‌های منطقی `ms-4` (شروع) و `me-4` (پایان) استفاده کنید تا در
`dir="rtl"` درست رفتار کنند.

## جلوگیری از تکرار

اگر یک ترکیب کلاس را مدام تکرار می‌کنید، آن را به یک **کامپوننت** (در قالب جنگو، React یا Vue) تبدیل کنید. برای
موارد خاص، می‌توانید در CSS با `@apply` کلاس بسازید:

```css
.btn {
  @apply rounded-full px-5 py-2 font-semibold;
}
```

## افزونهٔ ویرایشگر

افزونهٔ رسمی **Tailwind CSS IntelliSense** برای VS Code پیشنهاد خودکار کلاس و پیش‌نمایش رنگ‌ها را فراهم می‌کند.
""",
    ),
    dict(
        title="اسکریپت‌نویسی Bash: خودکار کردن کارهای تکراری",
        category="tutorials", type="tutorial", tags=["Bash", "Linux", "Automation"], label="BASH", photo="1550439062-609e1531270e",
        excerpt="هر کاری را که بیش از دو بار در ترمینال انجام می‌دهید، می‌شود در یک اسکریپت نوشت. متغیر، شرط، حلقه و "
                "تابع در Bash با مثال‌های کاربردی.",
        body=r"""## اولین اسکریپت

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "سلام، $(whoami)! امروز $(date +%F) است."
```

```bash
chmod +x hello.sh
./hello.sh
```

خط `set -euo pipefail` اسکریپت را امن‌تر می‌کند:

| گزینه | کارکرد |
|---|---|
| `-e` | با اولین خطا متوقف شو |
| `-u` | استفاده از متغیر تعریف‌نشده خطاست |
| `-o pipefail` | خطا در هر بخش از pipe، کل pipe را ناموفق می‌کند |

## متغیرها

```bash
name="mysite"
backup_dir="/var/backups/$name"
echo "Backup dir: $backup_dir"
```

- دور `=` فاصله نگذارید.
- متغیرها را همیشه داخل **دابل‌کوتیشن** بنویسید: `"$file"`، تا نام‌های فاصله‌دار خراب نشوند.

## ورودی‌های اسکریپت

```bash
# ./deploy.sh production
env="${1:-staging}"   # اگر آرگومان نبود، staging
echo "Deploying to $env"
```

## شرط

```bash
if [[ -f ".env" ]]; then
    echo ".env exists"
elif [[ -d "config" ]]; then
    echo "config dir exists"
else
    echo "nothing found" >&2
    exit 1
fi
```

| آزمون | معنی |
|---|---|
| `-f file` | فایل وجود دارد |
| `-d dir` | پوشه وجود دارد |
| `-z "$s"` | رشته خالی است |
| `"$a" == "$b"` | رشته‌ها برابرند |
| `$n -gt 5` | عدد بزرگ‌تر از ۵ |

## حلقه

```bash
for file in *.log; do
    gzip "$file"
done

while read -r line; do
    echo "Host: $line"
done < hosts.txt
```

## تابع

```bash
log() {
    echo "[$(date +%T)] $*"
}

log "Starting backup"
```

## مثال کامل: پشتیبان‌گیری با نگهداری ۷ نسخهٔ آخر

```bash
#!/usr/bin/env bash
set -euo pipefail

src="${1:?usage: backup.sh <directory>}"
dest="$HOME/backups"
mkdir -p "$dest"

archive="$dest/$(basename "$src")-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$archive" -C "$(dirname "$src")" "$(basename "$src")"
echo "Created $archive"

ls -1t "$dest"/*.tar.gz | tail -n +8 | xargs -r rm --
```

## ابزار کمکی

**ShellCheck** اسکریپت‌های Bash را بررسی می‌کند و اشتباه‌های رایج مثل فراموش کردن کوتیشن را گوشزد می‌کند:

```bash
shellcheck backup.sh
```
""",
    ),
    dict(
        title="استقرار جنگو با Gunicorn و Nginx روی سرور لینوکس",
        category="cloud-devops", type="tutorial", tags=["Django", "Nginx", "Deployment"], label="DEPLOY",
        photo="1571171637578-41bc2dd41cd2",
        excerpt="`runserver` برای توسعه است، نه برای کاربران واقعی. قدم‌به‌قدم یک پروژهٔ جنگو را با Gunicorn، systemd و "
                "Nginx روی سرور اوبونتو راه بیندازید.",
        body=r"""## معماری

```text
کاربر ⇄ Nginx (پورت 80/443) ⇄ Gunicorn (127.0.0.1:8000) ⇄ جنگو
              └── فایل‌های static و media مستقیم از دیسک
```

- **Gunicorn** کد پایتون را با چند worker اجرا می‌کند.
- **Nginx** درخواست‌ها را می‌گیرد، فایل‌های ایستا را سریع تحویل می‌دهد و بقیه را به Gunicorn می‌فرستد.

## ۱. آماده‌سازی پروژه

```bash
sudo apt update && sudo apt install -y python3-venv nginx
cd /srv && git clone https://github.com/USER/mysite.git && cd mysite
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt gunicorn
```

در تنظیمات production:

```python
DEBUG = False
ALLOWED_HOSTS = ["example.com", "www.example.com"]
STATIC_ROOT = BASE_DIR / "staticfiles"
```

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

## ۲. سرویس systemd برای Gunicorn

فایل `/etc/systemd/system/mysite.service`:

```ini
[Unit]
Description=mysite gunicorn
After=network.target

[Service]
User=www-data
WorkingDirectory=/srv/mysite
EnvironmentFile=/srv/mysite/.env
ExecStart=/srv/mysite/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mysite
sudo systemctl status mysite
```

یک قاعدهٔ رایج برای تعداد worker: `(2 × تعداد هسته‌ها) + 1`؛ سپس با اندازه‌گیری تنظیمش کنید.

## ۳. پیکربندی Nginx

فایل `/etc/nginx/sites-available/mysite`:

```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    client_max_body_size 20M;

    location /static/ {
        alias /srv/mysite/staticfiles/;
    }
    location /media/ {
        alias /srv/mysite/media/;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/mysite /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## ۴. به‌روزرسانی‌های بعدی

```bash
cd /srv/mysite && git pull
source .venv/bin/activate && pip install -r requirements.txt
python manage.py migrate && python manage.py collectstatic --noinput
sudo systemctl restart mysite
```

## ۵. عیب‌یابی

| علامت | جای بررسی |
|---|---|
| 502 Bad Gateway | `journalctl -u mysite -n 50`؛ Gunicorn اجرا نشده یا خطا داده |
| فایل‌های CSS بارگذاری نمی‌شوند | مسیر `alias` و اجرای `collectstatic` |
| 400 Bad Request | دامنه در `ALLOWED_HOSTS` نیست |

قدم بعدی و ضروری: فعال کردن HTTPS با Let's Encrypt.
""",
    ),
    dict(
        title="HTTPS رایگان با Let's Encrypt و Certbot",
        category="security", type="tutorial", tags=["HTTPS", "TLS", "Nginx"], label="HTTPS", photo="1525547719571-a2d4ac8945e2",
        excerpt="امروز دلیلی برای سایت بدون HTTPS وجود ندارد. با Certbot در چند دقیقه گواهی رایگان بگیرید، Nginx را "
                "تنظیم کنید و تمدید را خودکار کنید.",
        body=r"""## چرا HTTPS؟

- **محرمانگی:** رمزها و اطلاعات کاربران در مسیر قابل خواندن نیست.
- **یکپارچگی:** کسی نمی‌تواند در مسیر، تبلیغ یا کد مخرب به صفحه تزریق کند.
- **اعتماد و سئو:** مرورگرها سایت‌های HTTP را «ناامن» نشان می‌دهند.
- **قابلیت‌های مدرن:** HTTP/2، Service Worker و بسیاری از APIهای مرورگر فقط روی HTTPS کار می‌کنند.

## Let's Encrypt

مرجع صدور گواهی **رایگان و خودکار** که از سال ۲۰۱۵ کار خود را آغاز کرده است. گواهی‌هایش عمر کوتاهی دارند و برای
همین تمدید باید خودکار باشد. **Certbot** ابزار رسمی پیشنهادی برای دریافت و تمدید آن‌هاست.

## پیش‌نیازها

1. دامنه‌ای که رکورد A آن به IP سرور شما اشاره کند.
2. Nginx با یک `server_name` درست، که روی پورت 80 در دسترس باشد.

## نصب و دریافت گواهی

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com -d www.example.com
```

Certbot مالکیت دامنه را تأیید می‌کند، گواهی می‌گیرد و فایل تنظیم Nginx را به‌روز می‌کند تا روی پورت 443 گوش دهد
و HTTP را به HTTPS هدایت کند.

## تمدید خودکار

بستهٔ Certbot یک تایمر systemd نصب می‌کند. تست کنید:

```bash
systemctl list-timers | grep certbot
sudo certbot renew --dry-run
```

## سخت‌گیری بیشتر

### HSTS

به مرورگر می‌گوید از این به بعد فقط با HTTPS به سایت وصل شود:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

با مقدار کوچک شروع کنید؛ اگر HSTS فعال شود و بعداً HTTPS خراب شود، کاربران تا پایان max-age نمی‌توانند وارد سایت
شوند.

### تنظیمات جنگو

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 3600  # بعد از اطمینان، بیشترش کنید
```

`SECURE_PROXY_SSL_HEADER` را فقط وقتی تنظیم کنید که Nginx هدر `X-Forwarded-Proto` را خودش تنظیم می‌کند؛ وگرنه
کاربر می‌تواند این هدر را جعل کند.

## بررسی نتیجه

ابزار آنلاین **SSL Labs** پیکربندی TLS سرور شما را نمره‌دهی می‌کند و مشکلاتی مثل پروتکل‌های قدیمی را نشان می‌دهد.

## عیب‌یابی

| خطا | علت رایج |
|---|---|
| Challenge failed | رکورد DNS هنوز به سرور اشاره نمی‌کند یا پورت 80 بسته است |
| Too many certificates | محدودیت نرخ صدور؛ برای تست از `--staging` استفاده کنید |
| Mixed content | صفحه هنوز فایل‌هایی را با `http://` بارگذاری می‌کند |
""",
    ),
    dict(
        title="تحلیل داده با Pandas: از فایل CSV تا گزارش",
        category="ai", type="tutorial", tags=["Pandas", "Python", "Data Analysis"], label="PANDAS", photo="1518186285589-2f7649de83e0",
        excerpt="Pandas ابزار اصلی تحلیل داده در پایتون است. یک فایل فروش را بخوانید، تمیز کنید، گروه‌بندی کنید و از آن "
                "گزارش بگیرید.",
        body=r"""## نصب

```bash
pip install pandas
```

## خواندن داده

```python
import pandas as pd

df = pd.read_csv("sales.csv", parse_dates=["date"])
print(df.head())      # پنج ردیف اول
df.info()             # نوع ستون‌ها و مقادیر خالی
print(df.describe())  # آمار توصیفی ستون‌های عددی
```

فرض کنید ستون‌ها این‌ها هستند: `date`, `city`, `product`, `quantity`, `price`.

## انتخاب و فیلتر

```python
df["city"]                         # یک ستون (Series)
df[["product", "price"]]           # چند ستون
df[df["price"] > 1_000_000]        # فیلتر
df[(df["city"] == "Tehran") & (df["quantity"] >= 2)]
df.query("city == 'Tehran' and quantity >= 2")   # همان، خواناتر
```

دقت کنید در شرط‌های ترکیبی از `&` و `|` استفاده می‌شود، نه `and` و `or`، و هر شرط باید داخل پرانتز باشد.

## ستون جدید

```python
df["total"] = df["quantity"] * df["price"]
df["month"] = df["date"].dt.to_period("M")
```

## تمیز کردن داده

```python
df.isna().sum()                          # تعداد مقادیر خالی هر ستون
df = df.dropna(subset=["price"])          # حذف ردیف‌های بدون قیمت
df["city"] = df["city"].fillna("نامشخص")
df = df.drop_duplicates()
df["city"] = df["city"].str.strip()
```

## گروه‌بندی

```python
by_city = (
    df.groupby("city")
      .agg(orders=("total", "size"), revenue=("total", "sum"), avg=("total", "mean"))
      .sort_values("revenue", ascending=False)
)
print(by_city)
```

## جدول محوری

```python
pivot = df.pivot_table(index="month", columns="city", values="total", aggfunc="sum", fill_value=0)
```

## ادغام با جدول دیگر

```python
products = pd.read_csv("products.csv")   # product, category
df = df.merge(products, on="product", how="left")
```

## ذخیرهٔ نتیجه

```python
by_city.to_csv("report.csv", encoding="utf-8-sig")   # utf-8-sig تا اکسل فارسی را درست نشان دهد
by_city.to_excel("report.xlsx")                       # نیاز به بستهٔ openpyxl
```

## نکته‌های کارایی

- به‌جای حلقهٔ `for` روی ردیف‌ها، از عملیات برداری مثل `df["a"] * df["b"]` استفاده کنید؛ ده‌ها برابر سریع‌تر است.
- برای فایل‌های بسیار بزرگ، فقط ستون‌های لازم را بخوانید: `pd.read_csv(path, usecols=[...])`.
- اگر داده از حافظه بزرگ‌تر است، به ابزارهایی مثل **Polars** یا **DuckDB** نگاه کنید.
""",
    ),
    dict(
        title="رسم نمودار با Matplotlib: از نمودار خطی تا ذخیرهٔ تصویر",
        category="ai", type="tutorial", tags=["Matplotlib", "Python", "Data Visualization"], label="MATPLOTLIB",
        photo="1504868584819-f8e8b4b6d7e3",
        excerpt="داده‌ای که دیده نشود، فهمیده نمی‌شود. با Matplotlib نمودارهای خطی، میله‌ای و پراکندگی بسازید و آن‌ها را "
                "برای گزارش آماده کنید.",
        body=r"""## نصب

```bash
pip install matplotlib
```

## ساختار پایه: Figure و Axes

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot([1, 2, 3, 4], [10, 25, 18, 30])
ax.set_title("Monthly visits")
ax.set_xlabel("Month")
ax.set_ylabel("Visits (thousands)")
plt.show()
```

- **Figure:** کل بوم تصویر.
- **Axes:** یک نمودار درون بوم. یک Figure می‌تواند چند Axes داشته باشد.

همیشه با `fig, ax = plt.subplots()` شروع کنید؛ این سبک شیءگرا در نمودارهای پیچیده‌تر بسیار خواناتر است.

## نمودار خطی با چند سری

```python
months = ["Jan", "Feb", "Mar", "Apr", "May"]
fig, ax = plt.subplots()
ax.plot(months, [12, 18, 15, 22, 28], marker="o", label="Web")
ax.plot(months, [8, 9, 14, 16, 21], marker="s", label="Mobile")
ax.legend()
ax.grid(alpha=0.3)
```

## نمودار میله‌ای

```python
langs = ["Python", "JavaScript", "Go", "Rust"]
users = [48, 42, 14, 11]

fig, ax = plt.subplots()
bars = ax.bar(langs, users, color="#2563eb")
ax.bar_label(bars)
ax.spines[["top", "right"]].set_visible(False)
```

## نمودار پراکندگی

```python
ax.scatter(df["area"], df["price"], alpha=0.5)
```

## چند نمودار کنار هم

```python
fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4))
left.hist(df["price"], bins=30)
right.boxplot(df["price"])
fig.tight_layout()
```

## ذخیره

```python
fig.savefig("chart.png", dpi=200, bbox_inches="tight")
fig.savefig("chart.svg")   # برداری، برای چاپ و وب
```

## از Pandas مستقیم

```python
df.groupby("month")["total"].sum().plot(kind="bar", ax=ax)
```

## متن فارسی در نمودار

Matplotlib به‌تنهایی حروف فارسی را به هم نمی‌چسباند و راست‌به‌چپ نمی‌نویسد. دو راه:

1. برچسب‌ها را با دو بستهٔ `arabic-reshaper` و `python-bidi` آماده کنید و یک فونت فارسی (مثل وزیرمتن) تنظیم کنید.
2. برای نمودارهای وب، از کتابخانه‌های جاوااسکریپتی که RTL را پشتیبانی می‌کنند استفاده کنید.

## اصول یک نمودار خوب

- عنوان و برچسب محورها با واحد اندازه‌گیری
- محور عمودی نمودار میله‌ای از صفر شروع شود
- رنگ کم و هدفمند؛ رنگ را برای تأکید نگه دارید
- خطوط و حاشیه‌های اضافه را حذف کنید
""",
    ),
    dict(
        title="وب اسکرپینگ با Requests و BeautifulSoup، مسئولانه و درست",
        category="programming", type="tutorial", tags=["Web Scraping", "Python", "BeautifulSoup"],
        label="SCRAPING", photo="1624953587687-daf255b6b80a",
        excerpt="استخراج خودکار اطلاعات از صفحات وب، از پایش قیمت تا جمع‌آوری داده برای پژوهش. اصول فنی، و قواعدی که "
                "باید رعایت کنید.",
        body=r"""## قبل از شروع: قواعد

1. **اول دنبال API بگردید.** اگر سایت API رسمی دارد، از آن استفاده کنید.
2. **فایل `robots.txt` و شرایط استفادهٔ سایت** را بخوانید و رعایت کنید.
3. **سرور را آزار ندهید.** بین درخواست‌ها فاصله بگذارید.
4. **اطلاعات شخصی و محتوای دارای حق نشر** را بدون مجوز جمع‌آوری یا بازنشر نکنید.

## نصب

```bash
pip install requests beautifulsoup4
```

## دریافت صفحه

```python
import requests

headers = {"User-Agent": "MyResearchBot/1.0 (contact: me@example.com)"}
response = requests.get("https://example.com/articles", headers=headers, timeout=10)
response.raise_for_status()
html = response.text
```

همیشه `timeout` بگذارید؛ بدون آن، برنامه ممکن است برای همیشه منتظر بماند.

## تجزیهٔ HTML

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")

for card in soup.select("article.post"):
    title = card.select_one("h2").get_text(strip=True)
    link = card.select_one("a")["href"]
    print(title, link)
```

| متد | کاربرد |
|---|---|
| `select("css selector")` | همهٔ عناصر مطابق |
| `select_one(...)` | اولین عنصر یا None |
| `get_text(strip=True)` | متن بدون فاصله‌های اضافه |
| `el["href"]` / `el.get("href")` | خواندن صفت (attribute) |

## آدرس‌های نسبی

```python
from urllib.parse import urljoin

full_url = urljoin(response.url, link)
```

## چند صفحه، با احترام

```python
import time

session = requests.Session()
session.headers.update(headers)

for page in range(1, 6):
    r = session.get(f"https://example.com/articles?page={page}", timeout=10)
    if r.status_code == 429:   # Too Many Requests
        time.sleep(60)
        continue
    r.raise_for_status()
    parse(r.text)
    time.sleep(2)
```

## ذخیره

```python
import csv

with open("articles.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "url"])
    writer.writerows(rows)
```

## صفحه‌های پویا

اگر محتوا با جاوااسکریپت ساخته می‌شود، در HTML اولیه وجود ندارد. دو راه:

1. در زبانهٔ **Network** ابزار توسعه‌دهندهٔ مرورگر ببینید صفحه داده را از کدام API می‌گیرد.
2. از مرورگر خودکار مثل **Playwright** استفاده کنید (سنگین‌تر و کندتر).

## نگهداری

ساختار HTML سایت‌ها تغییر می‌کند. اسکرپر را با بررسی‌های ساده بنویسید (مثلاً اگر هیچ مقاله‌ای پیدا نشد، خطا بدهد)
تا خرابی بی‌صدا نماند.
""",
    ),
    dict(
        title="کارهای پس‌زمینه در جنگو با Celery و Redis",
        category="cloud-devops", type="tutorial", tags=["Celery", "Django", "Redis"], label="CELERY", photo="1538481199705-c710c4e965fc",
        excerpt="ارسال ایمیل، ساخت گزارش یا پردازش تصویر نباید کاربر را منتظر نگه دارد. این کارها را با Celery به صف "
                "پس‌زمینه بسپارید.",
        body=r"""## چرا صف کار؟

اگر ارسال ایمیل خوش‌آمدگویی ۳ ثانیه طول بکشد، کاربر بعد از ثبت‌نام ۳ ثانیه به صفحهٔ سفید نگاه می‌کند. با صف کار،
درخواست بلافاصله پاسخ می‌گیرد و یک **worker** جداگانه کار را در پس‌زمینه انجام می‌دهد.

```text
جنگو ──(کار)──► Redis (broker) ──► Celery worker
```

## نصب

```bash
pip install "celery[redis]"
# Redis را نصب یا با Docker اجرا کنید:
docker run -d -p 6379:6379 redis:7
```

## پیکربندی

فایل `config/celery.py`:

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

فایل `config/__init__.py`:

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

در `settings.py`:

```python
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_TASK_TIME_LIMIT = 300
```

## تعریف کار

فایل `accounts/tasks.py`:

```python
from celery import shared_task
from django.core.mail import send_mail

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id):
    from .models import User
    user = User.objects.get(pk=user_id)
    try:
        send_mail("خوش آمدید!", "از پیوستن شما خوشحالیم.", None, [user.email])
    except Exception as exc:
        raise self.retry(exc=exc)
```

## صدا زدن کار

```python
send_welcome_email.delay(user.id)
```

به کار **شناسهٔ کاربر** بدهید، نه خود شیء. داده باید قابل سریال‌سازی باشد و worker باید تازه‌ترین نسخه را از
دیتابیس بخواند.

### فقط بعد از commit تراکنش

```python
from django.db import transaction

transaction.on_commit(lambda: send_welcome_email.delay(user.id))
```

وگرنه ممکن است worker زودتر از ثبت نهایی کاربر در دیتابیس اجرا شود و او را پیدا نکند.

## اجرای worker

```bash
celery -A config worker -l info
```

## کارهای زمان‌بندی‌شده

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "weekly-digest": {
        "task": "newsletter.tasks.send_weekly_digest",
        "schedule": crontab(hour=10, minute=0, day_of_week="sat"),
    },
}
```

```bash
celery -A config beat -l info
```

## نکته‌ها

- کارها را **idempotent** بنویسید؛ یعنی اگر دو بار اجرا شوند، مشکلی پیش نیاید.
- برای پایش صف و کارها، ابزار **Flower** را امتحان کنید.
- برای پروژه‌های کوچک، گاهی یک دستور مدیریتی جنگو با cron ساده‌تر از Celery است.
""",
    ),
    dict(
        title="Decorator در پایتون: توابعی که توابع را تغییر می‌دهند",
        category="programming", type="tutorial", tags=["Python", "Decorator", "Advanced Python"],
        label="DECORATORS", photo="1515378791036-0648a3ef77b2",
        excerpt="`@login_required`، `@app.get` و `@lru_cache` همه decorator هستند. ببینید پشت این علامت @ چه می‌گذرد و "
                "decorator خودتان را بنویسید.",
        body=r"""## پیش‌نیاز: تابع هم یک شیء است

در پایتون می‌شود تابع را به متغیر داد، به تابع دیگر فرستاد یا از تابع برگرداند:

```python
def shout(text):
    return text.upper()

speak = shout
print(speak("hello"))   # HELLO
```

## decorator چیست؟

تابعی که یک تابع می‌گیرد و تابع جدیدی برمی‌گرداند. این دو کد معادل‌اند:

```python
@my_decorator
def greet(): ...

def greet(): ...
greet = my_decorator(greet)
```

## اولین decorator: زمان‌سنج

```python
import functools
import time

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

@timed
def slow_sum(n):
    return sum(range(n))

slow_sum(10_000_000)
```

### چرا `functools.wraps`؟

بدون آن، نام و docstring تابع اصلی گم می‌شود و `slow_sum.__name__` برابر `"wrapper"` خواهد بود؛ این کار دیباگ و
ابزارهای مستندسازی را به هم می‌ریزد.

## decorator با آرگومان

یک لایهٔ دیگر لازم است:

```python
def retry(times=3, delay=1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except ConnectionError:
                    if attempt == times:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(times=5, delay=2)
def fetch_rates():
    ...
```

## decoratorهای آماده و پرکاربرد

| decorator | کاربرد |
|---|---|
| `@functools.lru_cache` / `@functools.cache` | کش نتیجهٔ تابع بر اساس ورودی |
| `@property` | متد را مثل یک صفت قابل خواندن می‌کند |
| `@staticmethod` / `@classmethod` | متدهای بدون self یا با cls |
| `@dataclass` | ساخت خودکار `__init__` و `__repr__` |
| `@login_required` (جنگو) | محدود کردن ویو به کاربران واردشده |

```python
from functools import cache

@cache
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

fib(200)   # فوری، به لطف کش
```

## چند decorator روی هم

```python
@login_required
@require_POST
def delete_comment(request, pk): ...
```

ترتیب اعمال از **پایین به بالاست**: اول `require_POST` و بعد `login_required` تابع را می‌پیچد؛ اما در زمان اجرا،
اول بررسی `login_required` انجام می‌شود.

## کی decorator ننویسیم؟

اگر منطق فقط در یک جا استفاده می‌شود، یک تابع معمولی واضح‌تر است. decorator برای کارهای **تکراری و عرضی** مثل
لاگ، کش، مجوزدهی و تلاش دوباره مناسب است.
""",
    ),
]
