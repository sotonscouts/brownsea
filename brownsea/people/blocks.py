from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class PersonBlock(blocks.StructBlock):
    name = blocks.CharBlock()
    role = blocks.CharBlock()
    profile_picture = ImageChooserBlock()

    class Meta:
        template = "components/streamfield/blocks/person_block.html"
        icon = "user"
        label = "Person"


class PersonGroupBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    people = blocks.ListBlock(PersonBlock())

    class Meta:
        template = "components/streamfield/blocks/person_group_block.html"
        icon = "group"
        label = "Person Group"
