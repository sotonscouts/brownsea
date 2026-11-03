"""Icons that editors can choose for task tiles.

Editors pick a name, and each name maps to an icon class here. Names describe the meaning rather than the icon
library, so the library can be swapped by changing this mapping only.
"""

# name: (label shown to editors, Bootstrap Icons class)
TASK_ICONS = {
    "booking": ("Booking", "bi-calendar-check"),
    "calendar": ("Calendar", "bi-calendar3"),
    "camp": ("Camp", "bi-tree"),
    "contact": ("Contact", "bi-telephone"),
    "document": ("Document", "bi-file-earmark-text"),
    "download": ("Download", "bi-download"),
    "form": ("Form", "bi-ui-checks"),
    "help": ("Help", "bi-question-circle"),
    "link": ("Link", "bi-link-45deg"),
    "map": ("Map", "bi-geo-alt"),
    "money": ("Money", "bi-currency-pound"),
    "people": ("People", "bi-people"),
    "report": ("Report", "bi-clipboard-data"),
    "safeguarding": ("Safeguarding", "bi-shield-check"),
    "training": ("Training", "bi-mortarboard"),
    "video": ("Video", "bi-camera-video"),
    # User management
    "account": ("Account", "bi-person-circle"),
    "add-user": ("Add user", "bi-person-plus"),
    "remove-user": ("Remove user", "bi-person-dash"),
    "login": ("Sign in", "bi-box-arrow-in-right"),
    "password": ("Password", "bi-key"),
    "permissions": ("Permissions", "bi-person-check"),
    "security": ("Security", "bi-shield-lock"),
    "email-account": ("Email account", "bi-envelope-at"),
}

DEFAULT_TASK_ICON = "link"

TASK_ICON_CHOICES = [(name, label) for name, (label, _) in TASK_ICONS.items()]


def task_icon_class(name):
    return TASK_ICONS.get(name, TASK_ICONS[DEFAULT_TASK_ICON])[1]
