# coding=utf-8

from __future__ import unicode_literals

import json

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.utils import flatatt
from django.forms.widgets import SelectMultiple, Select
from django.utils.encoding import force_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext

from libs.attachtor.forms.widgets import RedactorAttachtorWidget
from libs.multilingo.forms import widgets as multilingo


class Select2Multiple(SelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        output = super(Select2Multiple, self).render(name, value, attrs, choices)
        return mark_safe(output + '<script>$("#%s").select2();</script>' % attrs['id'])


class Select2(Select):
    def render(self, name, value, attrs=None, choices=()):
        output = super(Select2, self).render(name, value, attrs, choices)
        return mark_safe(output + '<script>$("#%s").select2();</script>' % attrs['id'])


class ButtonSelectMixIn(object):
    def render(self, name, value, attrs=None, choices=()):
        if attrs is not None:
            opts = attrs.pop('buttonselect', {})
        else:
            opts = {}
        output = super(ButtonSelectMixIn, self).render(name, value, attrs, choices)
        return mark_safe(output + '<script>$("#%s").buttonSelect(%s);</script>' %
                         (attrs['id'], json.dumps(opts)))


class ButtonSelect(ButtonSelectMixIn, forms.Select):
    pass


class AutoSubmitButtonSelect(forms.Select):
    def render(self, name, value, attrs=None, choices=()):
        if attrs is not None:
            opts = attrs.pop('buttonselect', {})
        else:
            opts = {}
        opts['changeEvent'] = 'change'
        output = super(AutoSubmitButtonSelect, self).render(name, value, attrs, choices)
        return mark_safe(output + """
            <script>
                $("#%s").buttonSelect(%s).on('change', function() {
                    $(this).parents('form').first().submit();
                });
            </script>
            """ % (attrs['id'], json.dumps(opts)))


class SingleLanguageRedactorAttachtorWidget(multilingo.SingleLanguageWidgetMixIn,
                                            RedactorAttachtorWidget):
    pass


class MultiLingualWidget(multilingo.MultiLingualWidget):
    def get_options(self):
        opts = super(MultiLingualWidget, self).get_options()
        opts.update({
            'langChoiceText': ugettext("Kieliversiot")
        })
        return opts


class MultiLingualWidgetWithTranslatedNotification(MultiLingualWidget):

    def render(self, name, value, attrs=None):
        html = super(MultiLingualWidgetWithTranslatedNotification, self).render(
            name, value, attrs)

        fully_translated = True
        for i, widget in enumerate(self.widgets):
            widget_value = None
            if isinstance(value, dict):
                widget_value = value.get(self._lang_code(i), None)
            elif isinstance(value, list) and len(value) > i:
                widget_value = value[i]
            if not widget_value:
                fully_translated = False

        if fully_translated:
            html += '<span class="fully-translated">({})</span>'.format(
                ugettext("Käännetty"))
        return html


class NukaDateTimePicker(DateTimePicker):
    nuka_class = 'nuka-datetimepicker'

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        input_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        input_attrs['class'] = "{} {}".format(input_attrs['class'], self.nuka_class)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            input_attrs['value'] = force_text(self._format_value(value))
        input_attrs = dict([(key, conditional_escape(val))
                            for key, val in input_attrs.items()])  # python2.6 compatible
        if not self.picker_id:
            self.picker_id = input_attrs.get('id', '') + '_picker'
        self.div_attrs['id'] = self.picker_id
        picker_id = conditional_escape(self.picker_id)
        div_attrs = dict(
            [(key, conditional_escape(val)) for key, val in self.div_attrs.items()])  # python2.6 compatible
        icon_attrs = dict([(key, conditional_escape(val))
                           for key, val in self.icon_attrs.items()])
        html = self.html_template % dict(div_attrs=flatatt(div_attrs),
                                         input_attrs=flatatt(input_attrs),
                                         icon_attrs=flatatt(icon_attrs))
        if not self.options:
            js = ''
        else:
            options = json.dumps(self.options or {}, cls=DjangoJSONEncoder)
            js = self.js_template % dict(picker_id=picker_id, options=options)
        return mark_safe(force_text(html + js))
