import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0004_newstopic_articlepage_audiences_articlepage_topics"),
        ("people", "0002_people_teams_and_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="articlepage",
            name="author_role",
            field=models.ForeignKey(
                blank=True,
                help_text="Who wrote this, and the role they had at the time. Choose their role, not just their name, "
                "so the article keeps showing it after they move on.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="articles",
                to="people.personrole",
                verbose_name="Author",
            ),
        ),
    ]
