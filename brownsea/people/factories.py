import factory
from factory.django import DjangoModelFactory
from wagtail_factories import PageFactory

from brownsea.people.models import Person, PersonListingPage, PersonRole, PersonTeam


class PersonTeamFactory(DjangoModelFactory):
    class Meta:
        model = PersonTeam

    name = factory.Sequence(lambda n: f"Team {n}")
    sort_order = factory.Sequence(lambda n: n)


class PersonFactory(DjangoModelFactory):
    """`PersonFactory(role="County Commissioner")` gives them one current role; add more with `PersonRoleFactory`."""

    class Meta:
        model = Person

    name = factory.Sequence(lambda n: f"Person {n}")
    show_in_listing = False

    @factory.post_generation
    def role(self, create, extracted, **kwargs):
        if create and extracted:
            PersonRoleFactory(person=self, title=extracted, **kwargs)


class PersonRoleFactory(DjangoModelFactory):
    class Meta:
        model = PersonRole

    person = factory.SubFactory(PersonFactory)
    title = factory.Sequence(lambda n: f"Role {n}")
    is_current = True
    sort_order = factory.Sequence(lambda n: n)


class PersonListingPageFactory(PageFactory):
    """Pass `parent=` the home page. The people shown are the `PersonFactory`s with `show_in_listing=True`."""

    class Meta:
        model = PersonListingPage

    title = "People"
    slug = "people"
    introduction = "The volunteers who run our district"
