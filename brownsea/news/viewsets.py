from brownsea.core.viewsets import TaxonomyViewSet

from .models import NewsTopic, NewsType


class NewsTypeViewSet(TaxonomyViewSet):
    model = NewsType
    menu_label = "News Types"


class NewsTopicViewSet(TaxonomyViewSet):
    model = NewsTopic
    menu_label = "News Topics"
