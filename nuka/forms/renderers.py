# coding=utf-8

from __future__ import unicode_literals

from bootstrap3.forms import render_label

from libs.bs3extras.renderers import AccessibleWrapIdFieldRenderer, \
    InstructionedFieldRendererMixin
from libs.formidable.forms.renderers import InlineFormFieldRendererMixIn
from nuka.utils import render_popover


class PopoverFieldRendererMixin(object):
    def add_label(self, html):
        """ Append the popover glyphicon span after the label, if popover is set. """
        label = self.get_label()
        if label:
            label_html = render_label(
                label,
                label_for=self.field.id_for_label,
                label_class=self.get_label_class()
            )

            if hasattr(self.field.field, "popover"):
                html = label_html + render_popover(self.field.field.popover) + html
            else:
                html = label_html + html
        return html


class NukaFieldRenderer(InstructionedFieldRendererMixin, InlineFormFieldRendererMixIn,
                        PopoverFieldRendererMixin, AccessibleWrapIdFieldRenderer):
    pass

