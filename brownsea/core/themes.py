from dataclasses import dataclass

# Hex values match brownsea/static_src/scss/_variables.scss.
SCOUT_PURPLE = "#490499"
SCOUT_RED = "#ed3f23"
SCOUT_NAVY = "#003982"
SCOUT_BLUE = "#006ddf"

WHITE = "#ffffff"
BLACK = "#000000"
NAVBAR_LIGHT_BG = "var(--bs-tertiary-bg)"


@dataclass(frozen=True)
class ScoutTheme:
    slug: str
    label: str
    primary: str
    on_primary: str
    navbar_bg: str
    navbar_color: str

    def css_properties(self) -> dict[str, str]:
        return {
            "--theme-primary": self.primary,
            "--theme-on-primary": self.on_primary,
            "--theme-primary-rgb": hex_to_rgb(self.primary),
            "--theme-navbar-bg": self.navbar_bg,
            "--theme-navbar-color": self.navbar_color,
        }


def hex_to_rgb(hex_color: str) -> str:
    value = hex_color.removeprefix("#")
    return f"{int(value[0:2], 16)}, {int(value[2:4], 16)}, {int(value[4:6], 16)}"


THEMES: dict[str, ScoutTheme] = {
    theme.slug: theme
    for theme in (
        ScoutTheme(
            slug="white",
            label="White",
            primary=SCOUT_PURPLE,
            on_primary=WHITE,
            navbar_bg=NAVBAR_LIGHT_BG,
            navbar_color=BLACK,
        ),
        ScoutTheme(
            slug="purple",
            label="Purple",
            primary=SCOUT_PURPLE,
            on_primary=WHITE,
            navbar_bg=SCOUT_PURPLE,
            navbar_color=WHITE,
        ),
        ScoutTheme(
            slug="navy",
            label="Navy",
            primary=SCOUT_NAVY,
            on_primary=WHITE,
            navbar_bg=SCOUT_NAVY,
            navbar_color=WHITE,
        ),
        ScoutTheme(
            slug="blue",
            label="Blue",
            primary=SCOUT_BLUE,
            on_primary=WHITE,
            navbar_bg=SCOUT_BLUE,
            navbar_color=WHITE,
        ),
        ScoutTheme(
            slug="red",
            label="Red",
            primary=SCOUT_RED,
            on_primary=WHITE,
            navbar_bg=SCOUT_RED,
            navbar_color=WHITE,
        ),
    )
}

DEFAULT_THEME = THEMES["white"]


def get_theme(slug: str) -> ScoutTheme:
    return THEMES.get(slug, DEFAULT_THEME)
