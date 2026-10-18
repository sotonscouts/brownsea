class GoogleFormEmbedFinder:
    def accept(self, url):
        return "https://docs.google.com/forms" in url

    def find_embed(self, url, max_width=None):
        # Normalise the URL to ensure it has the embedded parameter
        if "viewform" in url and "embedded=true" not in url:
            joiner = "&" if "?" in url else "?"
            url = f"{url}{joiner}embedded=true"

        return {
            "title": "Google Form",
            "author_name": "Google Docs",
            "provider_name": "Google Forms",
            "type": "rich",
            "html": f'<iframe src="{url}" width="100%" height="800" frameborder="0" marginheight="0" marginwidth="0" style="border:none;">Loading…</iframe>',  # noqa: E501
            "width": 800,
            "height": 800,
        }
