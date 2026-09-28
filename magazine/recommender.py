"""Content-based recommendations and relevance ranking with TF-IDF.

The index is built from published articles (title, tags, category, excerpt, body)
and cached until content changes (see ``core.cache.content_version``).
"""

import difflib
import math
from collections import Counter, defaultdict

from django.core.cache import cache
from django.utils import timezone

from core.cache import content_version

from .textutils import strip_code, tokenize

FIELD_WEIGHTS = {"title": 3.0, "tags": 3.0, "category": 1.5, "excerpt": 2.0, "body": 1.0}
RECENCY_HALF_LIFE_DAYS = 30


def _document_terms(article, tag_names):
    counts = Counter()
    fields = {
        "title": article.title,
        "tags": " ".join(tag_names),
        "category": article.category.name,
        "excerpt": article.excerpt,
        "body": strip_code(article.body),
    }
    for field, text in fields.items():
        for token in tokenize(text):
            counts[token] += FIELD_WEIGHTS[field]
    return counts


def _l2(vector):
    norm = math.sqrt(sum(v * v for v in vector.values())) or 1.0
    return {k: v / norm for k, v in vector.items()}


def _cosine(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())


class Index:
    def __init__(self, vectors, idf, meta):
        self.vectors = vectors  # {article_id: {term: weight}}
        self.idf = idf          # {term: idf}
        self.meta = meta        # {article_id: (category_id, published_at timestamp, title tokens)}

    def vectorize(self, text):
        counts = Counter(tokenize(text))
        return _l2({t: (1 + math.log(c)) * self.idf[t] for t, c in counts.items() if t in self.idf})


def build_index():
    from .models import Article

    articles = list(Article.objects.published().select_related("category").prefetch_related("tags"))
    term_counts = {a.pk: _document_terms(a, [t.name for t in a.tags.all()]) for a in articles}
    df = Counter()
    for counts in term_counts.values():
        df.update(counts.keys())
    n = len(articles) or 1
    idf = {term: math.log((1 + n) / (1 + freq)) + 1 for term, freq in df.items()}
    vectors = {
        pk: _l2({t: (1 + math.log(c)) * idf[t] for t, c in counts.items()})
        for pk, counts in term_counts.items()
    }
    meta = {a.pk: (a.category_id, a.published_at.timestamp(), frozenset(tokenize(a.title))) for a in articles}
    return Index(vectors, idf, meta)


def get_index():
    key = f"recommender:index:{content_version()}"
    index = cache.get(key)
    if index is None:
        index = build_index()
        cache.set(key, index, 60 * 60 * 6)
    return index


def _recency(ts):
    age_days = max(0.0, (timezone.now().timestamp() - ts) / 86400)
    return 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS)


def similar_ids(article, limit=3):
    index = get_index()
    vector = index.vectors.get(article.pk)
    if not vector:
        return []
    category_id = article.category_id
    scores = []
    for pk, other in index.vectors.items():
        if pk == article.pk:
            continue
        score = _cosine(vector, other)
        if index.meta[pk][0] == category_id:
            score += 0.05
        score += 0.05 * _recency(index.meta[pk][1])
        scores.append((score, pk))
    scores.sort(reverse=True)
    return [pk for score, pk in scores[:limit] if score > 0.06]


def for_user_ids(user, limit=6):
    """Personal recommendations from likes, bookmarks, reading history and followed topics."""
    from interactions.models import Bookmark, Like, ReadingHistory, TopicFollow

    index = get_index()
    weights = defaultdict(float)
    for pk in ReadingHistory.objects.filter(user=user).values_list("article_id", flat=True)[:50]:
        weights[pk] += 1.0
    for pk in Like.objects.filter(user=user).values_list("article_id", flat=True)[:50]:
        weights[pk] += 3.0
    for pk in Bookmark.objects.filter(user=user).values_list("article_id", flat=True)[:50]:
        weights[pk] += 3.0
    followed = set(TopicFollow.objects.filter(user=user).values_list("category_id", flat=True))

    profile = defaultdict(float)
    for pk, weight in weights.items():
        for term, value in index.vectors.get(pk, {}).items():
            profile[term] += weight * value
    profile = _l2(profile) if profile else {}

    seen = set(ReadingHistory.objects.filter(user=user).values_list("article_id", flat=True))
    scores = []
    for pk, vector in index.vectors.items():
        if pk in seen:
            continue
        score = _cosine(profile, vector) if profile else 0.0
        if index.meta[pk][0] in followed:
            score += 0.15
        score += 0.1 * _recency(index.meta[pk][1])
        scores.append((score, pk))
    scores.sort(reverse=True)
    return [pk for _, pk in scores[:limit]]


def rank_ids(query, candidate_ids):
    """Order candidate article ids by TF-IDF similarity to the query (title matches boosted)."""
    index = get_index()
    qvec = index.vectorize(query)
    qtokens = set(tokenize(query))

    def score(pk):
        title = index.meta.get(pk, (0, 0, frozenset()))[2]
        title_hits = len(qtokens & title) / len(qtokens) if qtokens else 0
        return _cosine(qvec, index.vectors.get(pk, {})) + 0.3 * title_hits

    scored = [(score(pk), pk) for pk in candidate_ids]
    scored.sort(key=lambda item: (-item[0], -index.meta.get(item[1], (0, 0, None))[1]))
    return [pk for _, pk in scored]


def correct_query(query):
    """Replace unknown query words with the closest word in the site's vocabulary ("pyton" -> "python")."""
    index = get_index()
    vocabulary = list(index.idf)
    corrected, changed = [], False
    for token in tokenize(query):
        if token in index.idf or len(token) < 3:
            corrected.append(token)
            continue
        match = difflib.get_close_matches(token, vocabulary, n=1, cutoff=0.75)
        corrected.append(match[0] if match else token)
        changed = changed or bool(match)
    return " ".join(corrected) if changed else ""


def fuzzy_ids(query, limit=6):
    """Loose OR-match on any query term: used for "similar results" when nothing matches exactly."""
    index = get_index()
    qvec = index.vectorize(query)
    if not qvec:
        return []
    scored = sorted(((_cosine(qvec, v), pk) for pk, v in index.vectors.items()), reverse=True)
    return [pk for score, pk in scored[:limit] if score > 0]
