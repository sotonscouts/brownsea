from django.contrib.auth.models import Permission
from wagtail import hooks


@hooks.register("register_permissions")
def register_restricted_map_permission():
    return Permission.objects.filter(content_type__app_label="standard_pages", codename="view_restricted_map")
