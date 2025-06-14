from wagtail import blocks


class LinkStructValue(blocks.StructValue):
    def get_link_text(self):
        if title := self.get("title"):
            return title

        # Handle instance where the page referenced is deleted.
        if page := self.get("page"):
            return page.title

        return ""

    def get_url(self):
        if external_url := self.get("external_url"):
            return external_url

        # Handle instance where the page referenced is deleted.
        if page := self.get("page"):
            return page.specific.url

        return ""
