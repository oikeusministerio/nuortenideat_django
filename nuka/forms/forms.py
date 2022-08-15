# coding=utf-8

from __future__ import unicode_literals

from nuka.utils import strip_emojis

from math import ceil
from fuzzywuzzy import fuzz


class HiddenLabelMixIn(object):
    def __init__(self, *args, **kwargs):
        super(HiddenLabelMixIn, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.label:
                field.widget.attrs["aria-label"] = field.label
            field.label = ""


class PopoverFormMixin(object):
    """ Sets popover attribute to the fields defined in the class' meta. """
    def __init__(self, *args, **kwargs):
        super(PopoverFormMixin, self).__init__(*args, **kwargs)
        if hasattr(self.Meta, "popovers"):
            for field_name, popover in self.Meta.popovers.iteritems():
                self.fields[field_name].popover = popover


class StripEmojisMixin(object):
    strip_emoji_fields = []

    def clean(self):
        if self.strip_emoji_fields:
            for field in self.strip_emoji_fields:
                if field in self.cleaned_data:
                    self.cleaned_data[field] = strip_emojis(self.cleaned_data[field])
        return super(StripEmojisMixin, self).clean()


class WordSearchMixin(object):
    search_text_field = 'search_text'
    default_order_by = ''
    pk_order_field = 'id'
    WORD_MIN_SCORE = 75
    MULTI_WORD_MIN_SCORE = 75

    def get_hit(self, score):
        hit = True if score >= self.WORD_MIN_SCORE else False
        return hit, score

    def get_multiword_hit(self, scores):
        hit = False
        total = sum(scores)
        score_passes = True if scores else False
        for score in scores:
            if score < self.MULTI_WORD_MIN_SCORE:
                score_passes = False

        if score_passes:
            hit = True

        return hit, total

    def get_scores(self, haystacks, words, method, sum_scores=False):
        scores = []
        for hay in haystacks:
            for word in words:
                scores.append(getattr(fuzz, method)(word, hay))
            return sum(scores) if sum_scores else scores

    def score_word(self, word, haystacks, multi_word=False):
        if multi_word:
            words = word.split(' ')
            scores = self.get_scores(haystacks, words, 'partial_token_sort_ratio')
            return self.get_multiword_hit(scores)
        else:
            score = self.get_scores(haystacks, [word], 'partial_token_sort_ratio',
                                    sum_scores=True)
            return self.get_hit(score)

    def get_haystack(self, obj):
        return [getattr(obj, self.search_text_field), ]

    def contains_words(self, qs, words):
        filters = {}
        for w in words.split(' '):
            word = w if len(w) < 4 else w[:int(ceil(0.7 * len(w)))]
            search_field = "{}__icontains".format(self.search_text_field)
            filters.update({search_field: word})

        if filters:
            return qs.filter(**filters)
        return qs

    def order_qs_with_pk_list(self, qs, pk_list):
        pk_str = ",".join(map(str, pk_list))
        return qs.extra(
            select={'manual': "FIELD({},{})".format(self.pk_order_field, pk_str)},
            order_by=['manual']
        )

    def word_search(self, word, qs, order_by=True):
        hits = []
        multi_word = len(word.split()) > 1
        qs = self.contains_words(qs, word)

        for o in qs.order_by(self.default_order_by):
            haystacks = self.get_haystack(o)
            hit, score = self.score_word(word, haystacks, multi_word=multi_word)
            if hit:
                hits.append((o.pk, score))

        hits.sort(key=lambda h: h[1], reverse=True)
        pk_list = [pk for pk, s in hits]
        qs = qs.filter(pk__in=pk_list)

        if order_by:
            qs = self.order_qs_with_pk_list(qs, pk_list)
        return qs
