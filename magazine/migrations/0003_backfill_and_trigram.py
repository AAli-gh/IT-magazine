from django.db import migrations


def enable_trigram(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def backfill(apps, schema_editor):
    from magazine.textutils import normalize, strip_code

    Article = apps.get_model("magazine", "Article")
    for article in Article.objects.select_related("category").prefetch_related("tags"):
        tags = " ".join(t.name for t in article.tags.all())
        article.search_text = normalize(" ".join(
            [article.title, article.excerpt, article.category.name, tags, strip_code(article.body)]))
        # Existing articles were published before notifications existed: don't notify now.
        if article.status == "published":
            article.notified_at = article.published_at
        article.save(update_fields=["search_text", "notified_at"])


class Migration(migrations.Migration):
    dependencies = [("magazine", "0002_newssource_alter_article_options_and_more")]

    operations = [
        migrations.RunPython(enable_trigram, migrations.RunPython.noop),
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
