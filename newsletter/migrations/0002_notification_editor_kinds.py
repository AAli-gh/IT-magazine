from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("newsletter", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("new_article", "مطلب جدید"),
                    ("reply", "پاسخ به دیدگاه"),
                    ("review", "مطلب در انتظار بررسی"),
                    ("moderation", "دیدگاه در انتظار تأیید"),
                ],
                max_length=20,
            ),
        ),
    ]
