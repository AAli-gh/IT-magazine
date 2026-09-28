import django.contrib.postgres.search
from django.db import migrations

INDEX = "magazine_article_search_vector_gin"


def create_index_and_backfill(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(f"CREATE INDEX IF NOT EXISTS {INDEX} ON magazine_article USING gin (search_vector)")
    schema_editor.execute(
        "UPDATE magazine_article SET search_vector = "
        "setweight(to_tsvector('simple', coalesce(lower(title), '')), 'A') || "
        "setweight(to_tsvector('simple', coalesce(search_text, '')), 'D')"
    )


def drop_index(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(f"DROP INDEX IF EXISTS {INDEX}")


class Migration(migrations.Migration):
    dependencies = [("magazine", "0004_article_author_blank")]

    operations = [
        migrations.AddField(
            model_name="article",
            name="search_vector",
            field=django.contrib.postgres.search.SearchVectorField(editable=False, null=True),
        ),
        migrations.RunPython(create_index_and_backfill, drop_index),
    ]
