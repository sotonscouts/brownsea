from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0006_copy_authors_to_people"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="articlepage",
            name="author",
        ),
    ]
