from django.utils.html import escape, format_html_join
from django.utils.safestring import mark_safe


class HtmlUtils:
    BULLET = "<b>&bull;</b>"
    EN_DASH = "&ndash;"

    @staticmethod
    def block_join(object_collection, sep=BULLET, multiline=True):
        if len(object_collection) == 0:
            return ""

        tag = f'<div style="{"display: inline-block; " if not multiline else ""}white-space: nowrap;">'
        if multiline:
            return format_html_join(
                "", f"{tag}{sep} {{}}</div>",
                ((str(obj),) for obj in object_collection)
            )
        else:
            if len(object_collection) > 1:
                everything_except_first = format_html_join(
                    "", f" {tag}{sep} {{}}</div>",
                    ((str(obj),) for obj in object_collection[1:])
                )
            else:
                everything_except_first = ""
            return mark_safe(f"{tag}{escape(object_collection[0])}</div>{everything_except_first}")
