from django.db import migrations

FALLBACK_ROLE_TITLE = "Volunteer"


def copy_authors_to_people(apps, schema_editor):
    Author = apps.get_model("core", "Author")
    Person = apps.get_model("people", "Person")
    PersonRole = apps.get_model("people", "PersonRole")
    ArticlePage = apps.get_model("news", "ArticlePage")

    for author in Author.objects.all():
        person = Person.objects.create(name=author.name, profile_picture_id=author.profile_picture_id)
        # Articles point at a role, so an author without one still gets a role to keep their articles attributed.
        role = PersonRole.objects.create(
            person=person,
            title=(author.role.strip() or FALLBACK_ROLE_TITLE)[:255],
            sort_order=0,
        )
        ArticlePage.objects.filter(author_id=author.pk).update(author_role=role)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_audience"),
        ("news", "0005_articlepage_author_role"),
        ("people", "0002_people_teams_and_roles"),
    ]

    operations = [
        migrations.RunPython(copy_authors_to_people, migrations.RunPython.noop),
    ]
