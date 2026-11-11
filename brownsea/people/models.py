from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, HelpPanel, InlinePanel
from wagtail.models import Orderable
from wagtail.search import index

from brownsea.core.models import BasePage, BrownseaPreviewableMixin


class PersonListingPage(BasePage):
    template = "pages/people/people_listing_page.html"
    max_count = 1

    introduction = models.TextField()

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        HelpPanel(
            "People are listed automatically: everyone with Show in listing ticked, under the teams of their "
            "current roles. Manage people and teams under People in the menu."
        ),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
    ]

    def get_sections(self):
        """
        The people to list, as sections in team order, each with its people by role priority then name.

        Someone with current roles in two teams is in both sections, with that team's roles, ranked by the highest
        priority among them. Roles with no team, and people with no current role, come last.
        """
        by_team = {}
        for person in Person.objects.filter(show_in_listing=True).prefetch_related("roles__team"):
            roles = person.current_roles
            for team_id in {role.team_id for role in roles} or {None}:
                team_roles = [role for role in roles if role.team_id == team_id]
                priority = max((role.priority for role in team_roles), default=0)
                by_team.setdefault(team_id, []).append({"person": person, "roles": team_roles, "priority": priority})

        def section(name, entries):
            return {
                "name": name,
                "entries": sorted(entries, key=lambda entry: (-entry["priority"], entry["person"].name.lower())),
            }

        sections = [section(team.name, by_team[team.pk]) for team in PersonTeam.objects.all() if team.pk in by_team]
        if None in by_team:
            sections.append(section("Other roles" if sections else None, by_team[None]))
        return sections

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["sections"] = self.get_sections()
        return context


class PersonTeam(index.Indexed, Orderable):
    """A group of people shown together on the people page, such as the district team or the trustees."""

    name = models.CharField(max_length=255)

    panels = [FieldPanel("name")]

    search_fields = [
        index.SearchField("name", boost=2),
        index.AutocompleteField("name"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return self.name


class PersonForm(WagtailAdminModelForm):
    def clean(self):
        cleaned_data = super().clean()
        # Articles record the role their author had, so a role they use can only be retired, not removed.
        for form in self.formsets["roles"].deleted_forms:
            if form.instance.pk and form.instance.articles.exists():
                raise ValidationError(
                    f"'{form.instance.title}' is the recorded role on an article, so it can't be removed. "
                    "Untick Current instead."
                )
        return cleaned_data


class Person(index.Indexed, BrownseaPreviewableMixin, ClusterableModel):
    """Someone who writes articles or appears on the people page, with the roles they hold or have held."""

    name = models.CharField(max_length=255)
    profile_picture = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="An optional picture. Without one, the first letter of the name is shown.",
    )
    show_in_listing = models.BooleanField(
        "Show in listing",
        default=False,
        help_text="Show this person on the people page, under the teams of their current roles.",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("profile_picture"),
        FieldPanel("show_in_listing"),
        InlinePanel(
            "roles",
            label="Role",
            heading="Roles",
            help_text="Drag to set the order. Untick Current when someone leaves a role, but keep it so older "
            "articles can still show it.",
        ),
    ]
    base_form_class = PersonForm

    search_fields = [
        index.SearchField("name", boost=2),
        index.AutocompleteField("name"),
        index.RelatedFields("roles", [index.SearchField("title")]),
    ]

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "people"

    def __str__(self):
        return self.name

    @property
    def current_roles(self):
        return [role for role in self.roles.all() if role.is_current]

    @property
    def primary_role(self):
        """The role to show when only one can be, such as in a preview."""
        roles = self.current_roles or list(self.roles.all())
        return roles[0] if roles else None

    def get_preview_template(self, request, mode_name):
        return "components/person_preview.html"


class PersonRole(index.Indexed, Orderable):
    person = ParentalKey(Person, on_delete=models.CASCADE, related_name="roles")
    title = models.CharField(max_length=255, help_text="For example, District Lead Volunteer.")
    team = models.ForeignKey(
        PersonTeam,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="roles",
        help_text="The group they are listed under on the people page.",
    )
    is_current = models.BooleanField("Current", default=True)
    priority = models.PositiveSmallIntegerField(
        default=0,
        help_text="Within a team on the people page, higher numbers are listed first. People with the same "
        "priority are listed alphabetically.",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("team"),
        FieldPanel("is_current"),
        FieldPanel("priority"),
    ]

    # Roles are picked on articles, so they can be found by the person's name or the role's title.
    search_fields = [
        index.SearchField("title", boost=2),
        index.AutocompleteField("title"),
        index.RelatedFields("person", [index.SearchField("name"), index.AutocompleteField("name")]),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        suffix = "" if self.is_current else " (past role)"
        return f"{self.person.name}, {self.title}{suffix}"
