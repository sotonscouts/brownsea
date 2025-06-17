from wagtail import hooks


@hooks.register("register_icons")
def register_icons(icons):
    return icons + ["icons/bullhorn.svg"]
