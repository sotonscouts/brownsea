from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_audience"),
        ("news", "0007_remove_articlepage_author"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Author",
        ),
    ]
