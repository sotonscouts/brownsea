from wagtail import hooks
from wagtail.admin.views.generic.chooser import ChooseResultsView, ChooseView
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import Person, PersonRole, PersonTeam


class PersonViewSet(SnippetViewSet):
    model = Person
    menu_label = "People"
    list_display = ("name", "show_in_listing")
    search_fields = ("name",)
    icon = "user"


class PersonTeamViewSet(SnippetViewSet):
    model = PersonTeam
    menu_label = "Teams"
    list_display = ("name",)
    search_fields = ("name",)
    icon = "group"


@register_snippet
class PeopleViewSetGroup(SnippetViewSetGroup):
    menu_label = "People"
    menu_icon = "group"
    items = (PersonViewSet, PersonTeamViewSet)


class PersonRoleChooseMixin:
    def get_object_list(self):
        return PersonRole.objects.select_related("person").order_by("person__name", "sort_order")


class PersonRoleChooseView(PersonRoleChooseMixin, ChooseView):
    pass


class PersonRoleChooseResultsView(PersonRoleChooseMixin, ChooseResultsView):
    pass


class PersonRoleChooserViewSet(ChooserViewSet):
    """
    Picks a person by one of their roles, such as "Sam Smith, District Commissioner".

    Roles are managed on the person, so there is no way to create one from the chooser.
    """

    model = PersonRole
    icon = "user"
    choose_one_text = "Choose an author"
    choose_another_text = "Choose another author"
    page_title = "Choose an author"
    choose_view_class = PersonRoleChooseView
    choose_results_view_class = PersonRoleChooseResultsView


person_role_chooser_viewset = PersonRoleChooserViewSet("person_role_chooser", url_prefix="person-role-chooser")


@hooks.register("register_admin_viewset")
def register_person_role_chooser_viewset():
    return person_role_chooser_viewset
