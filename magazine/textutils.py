"""Persian/English text normalization, tokenization and a tech synonym map."""

import re

_CHAR_MAP = str.maketrans({
    "ي": "ی", "ى": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "و",
    "‌": " ", "‏": "", "‎": "", "ـ": "",
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4", "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
})
_DIACRITICS = re.compile(r"[ً-ٰٟ]")
_TOKEN = re.compile(r"[\w\+\#\.]+", re.UNICODE)
_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)

STOPWORDS = set("""
و در به از که این را با است برای آن یک تا هم بر می شود شده های ها یا اما اگر نیز باید کرد کند کنید کنیم
دارد دارند بود بودن هر همه چه چی ما شما آنها ایشان خود نه بی پس سپس روی زیر بین درباره طور مثل مانند
the a an of to in and or is are was were be for on with as at by from it this that these those you we
""".split())

# Groups of equivalent terms; a query token matches any member of its group.
SYNONYM_GROUPS = [
    ["ai", "هوش مصنوعی", "هوش‌مصنوعی"],
    ["ml", "machine learning", "یادگیری ماشین"],
    ["deep learning", "یادگیری عمیق", "dl"],
    ["llm", "مدل زبانی", "مدل های زبانی", "large language model"],
    ["python", "پایتون"],
    ["django", "جنگو"],
    ["javascript", "js", "جاوااسکریپت", "جاوا اسکریپت"],
    ["typescript", "ts", "تایپ اسکریپت"],
    ["java", "جاوا"],
    ["security", "امنیت", "امنیت سایبری", "cybersecurity"],
    ["database", "db", "دیتابیس", "پایگاه داده"],
    ["web", "وب"],
    ["frontend", "فرانت اند", "فرانت‌اند"],
    ["backend", "بک اند", "بک‌اند"],
    ["devops", "دواپس"],
    ["cloud", "ابر", "کلود", "رایانش ابری"],
    ["kubernetes", "k8s", "کوبرنتیز"],
    ["docker", "داکر"],
    ["linux", "لینوکس"],
    ["android", "اندروید"],
    ["ios", "آی او اس"],
    ["gpu", "کارت گرافیک", "پردازنده گرافیکی"],
    ["cpu", "پردازنده"],
    ["open source", "متن باز", "متن‌باز", "اوپن سورس"],
    ["tutorial", "آموزش"],
    ["news", "خبر", "اخبار"],
    ["api", "ای پی آی"],
    ["game", "گیم", "بازی"],
    ["transformer", "ترنسفورمر"],
    ["crypto", "رمزنگاری", "cryptography"],
]


def normalize(text):
    text = (text or "").translate(_CHAR_MAP)
    text = _DIACRITICS.sub("", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def tokenize(text, drop_stopwords=True):
    tokens = _TOKEN.findall(normalize(text))
    tokens = [t.strip(".") for t in tokens]
    return [t for t in tokens if t and (not drop_stopwords or (t not in STOPWORDS and len(t) > 1))]


def strip_code(markdown_text):
    return _CODE_BLOCK.sub(" ", markdown_text or "")


_SYNONYMS = {}
for group in SYNONYM_GROUPS:
    normalized = [normalize(term) for term in group]
    for term in normalized:
        _SYNONYMS[term] = normalized


def expand_query(query):
    """Split a query into terms, each with its synonyms.

    Multi-word synonyms ("هوش مصنوعی") are detected first so they stay one term.
    Returns a list of lists: AND across the outer list, OR inside each inner list.
    """
    q = normalize(query)
    groups = []
    for phrase in sorted((k for k in _SYNONYMS if " " in k), key=len, reverse=True):
        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", q):
            groups.append(_SYNONYMS[phrase])
            q = re.sub(rf"(?<!\w){re.escape(phrase)}(?!\w)", " ", q)
    for token in tokenize(q):
        groups.append(_SYNONYMS.get(token, [token]))
    return groups
