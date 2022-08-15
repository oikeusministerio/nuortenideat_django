# coding=utf-8

from __future__ import unicode_literals

import random
from operator import attrgetter
from random import randint

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.aggregates import Count
from django.http.response import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.template import loader, TemplateDoesNotExist, Engine, Context
from django.utils.translation import override
from django.views.decorators.csrf import requires_csrf_token
from django.views.generic.base import RedirectView, TemplateView, View
from content.admin import InitiativeResource
from libs.djcontrib.views.generic import MultiModelFormView
from nkpicturecarousel.models import PictureCarouselSet, PictureCarouselImage

from nuka.utils import chunks
from content.models import Idea, Initiative
from tagging.utils import tags_by_popularity


class PictureCarousel(object):
    picture = "ni_kuvakaruselli_{}_lg.jpg"
    # picture_large = "ni_kuvakaruselli_{}_1140-2560_{}.jpg"
    # picture_medium = "ni_kuvakaruselli_{}_940-2560_{}.jpg"
    # picture_small = "ni_kuvakaruselli_{}_940x330_{}.jpg"
    # picture_alt = ""
    # picture_title = ""

    def __init__(self, language):
        image_sets = PictureCarouselSet.objects.annotate(
            images_count=Count("images")
        ).filter(
            is_active=True,
            images_count__gt=0
        )
        if image_sets:
            image_set = random.choice(image_sets)
            image = image_set.images.first()
            # image_sets_len = len(image_sets)
            # if image_sets_len == 1:
            #     image_set = image_sets[0]
            # else:
            #     random_number = randint(0, image_sets_len - 1)
            #     image_set = image_sets[random_number]

            # try:
            #     image = image_set.images.get(language=language)
            # except PictureCarouselImage.DoesNotExist:
            #     image = image_set.images.first()

            self.picture = image.original.url
            # self.picture_large = image.image_large.url
            # self.picture_medium = image.image_medium.url
            # self.picture_small = image.image_small.url
            self.picture_alt = image.alt_text.capitalize()

        else:
            pic_choices = ["1", "2", "3", "4", "5", "6"]
            # pic_choices = {
            #     "fi": ("ideoi", "kannata", "kommentoi"),
            #     "sv": ("föreslå", "gilla", "kommentera")
            # }

            # pic_alt_text_choices = {
            #     "fi": ("Nuoria harrastusten parissa.", "Nuoria erilaisissa tapahtumissa.", "Nuoria opiskelemassa."),
            #     "sv": ("Ungdomar i sina hobbyer.", "Ungdomar vid olika evenemang.", "Ungdomar studerar.")
            # }

            random_number = randint(0, 5)
            randomed_pic = pic_choices[random_number]
            # randomed_pic = pic_choices["fi"][random_number]

            # self.picture_alt = pic_alt_text_choices[language][random_number]
            # self.picture_title = pic_choices[language][random_number].capitalize()

            # img_path = "nuka/img/karuselli kieliversiot/"
            img_path = "nuka/img/karuselli/"
            self.picture = static(
                img_path + self.picture.format(randomed_pic)
            )
            # self.picture_large = static(
            #     img_path + self.picture_large.format(randomed_pic, language)
            # )
            # self.picture_medium = static(
            #     img_path + self.picture_medium.format(randomed_pic, language)
            # )
            # self.picture_small = static(
            #     img_path + self.picture_small.format(randomed_pic, language)
            # )


class PreFetchedObjectMixIn(object):
    obj_kwarg = 'obj'

    def get_object(self, queryset=None):
        return self.kwargs[self.obj_kwarg]


class IdeaBaseView(TemplateView):
    """ Returns a limited amount of initiatives. Allows sorting. """
    user_initiatives_count = 8
    organization_initiatives_count = 4
    SORT_NEWEST = 0
    SORT_POPULARITY = 6
    sorting = SORT_NEWEST

    def set_sorting(self):
        order_by = self.request.GET.get("jarjestys")
        if order_by == "uusin":
            self.sorting = self.SORT_NEWEST
        elif order_by == "suosituin":
            self.sorting = self.SORT_POPULARITY

    def get_user_ideas(self):
        ideas_user = Idea.objects.filter(
            visibility=Initiative.VISIBILITY_PUBLIC,
            initiator_organization_id__isnull=True
        ).order_by("-published")[:self.user_initiatives_count]
        ideas_user = ideas_user.prefetch_related(
                        'owners__settings',
                        'target_organizations')\
            .defer('target_organizations__description')

        return ideas_user

    def get_organization_ideas(self):
        ideas_organization = Idea.objects.filter(
            visibility=Initiative.VISIBILITY_PUBLIC,
            initiator_organization_id__isnull=False
        ).order_by("-published")[:self.organization_initiatives_count]
        ideas_organization = ideas_organization.prefetch_related(
                'owners__settings',
                'target_organizations')\
            .defer('target_organizations__description')

        return ideas_organization

    def set_user_ideas(self):
        if self.request.GET.get("jarjestys"):
            ideas_user = self.get_sorted_user_ideas()
        else:
            ideas_user = self.get_user_ideas()

        return ideas_user

    def set_organization_ideas(self):
        if self.request.GET.get("jarjestys"):
            ideas_organization = self.get_sorted_organization_ideas()
        else:
            ideas_organization = self.get_organization_ideas()

        return ideas_organization

    def get_sorted_user_ideas(self):
        self.set_sorting()

        if self.sorting == self.SORT_NEWEST:
            ideas_user = self.get_user_ideas()
        elif self.sorting == self.SORT_POPULARITY:
            ideas_user = Idea.objects.filter(
                visibility=Initiative.VISIBILITY_PUBLIC,
                initiator_organization_id__isnull=True
            )[:self.user_initiatives_count]
            ideas_user = sorted(ideas_user,
                                key=attrgetter("popularity"),
                                reverse=True)

        return ideas_user

    def get_sorted_organization_ideas(self):
        self.set_sorting()

        if self.sorting == self.SORT_NEWEST:
            ideas_organization = self.get_organization_ideas()
        elif self.sorting == self.SORT_POPULARITY:
            ideas_organization = Idea.objects.filter(
                visibility=Initiative.VISIBILITY_PUBLIC,
                initiator_organization_id__isnull=False
            )[:self.organization_initiatives_count]
            ideas_organization = sorted(ideas_organization,
                                        key=attrgetter("popularity"),
                                        reverse=True)

        return ideas_organization

    def get_context_data(self, **kwargs):
        context = super(IdeaBaseView, self).get_context_data(**kwargs)
        ideas_user = self.set_user_ideas()
        ideas_organization = self.set_organization_ideas()
        context["object_list_user"] = ideas_user
        context["object_list_organization"] = ideas_organization

        return context


class FrontPageContentView(IdeaBaseView, TemplateView):
    template_name = 'content/initiative_elements_all.html'

    def get_context_data(self, **kwargs):
        context = super(FrontPageContentView, self).get_context_data(**kwargs)
        return context


class FrontPageView(FrontPageContentView, TemplateView):
    template_name = 'nuka/frontpage.html'

    def get_context_data(self, **kwargs):
        context = super(FrontPageView, self).get_context_data(**kwargs)
        context["carousel"] = PictureCarousel(self.request.LANGUAGE_CODE)
        return context


class SitemapView(TemplateView):
    template_name = 'nuka/nuka_sitemap.html'


class FrontPageLocaleRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            with override(language=self.request.user.settings.language):
                return reverse('frontpage')
        return reverse('frontpage')


class AllowedFileUploadExtensions(View):
    def get(self, request, **kwargs):
        return HttpResponse("\n".join(sorted(settings.FILE_UPLOAD_ALLOWED_EXTENSIONS)),
                            content_type='text/plain')


class JsonMultiModelFormView(MultiModelFormView):
    form_template_name_syntax = None
    form_default_template = None
    preview_template_name_syntax = None

    def render_to_response(self, context, preview=False, reload=False, **response_kwargs):
        data = {}
        if preview:
            items = self.form_classes
            context = self.get_preview_context()
        else:
            items = context['forms'].items()

        for prefix, form in items:
            template_names = self.get_form_template_names(prefix, preview)

            if not preview:
                context = self.get_form_context(form)

            data[prefix] = render_to_string(
                template_names,
                RequestContext(self.request, context)
            )

        return JsonResponse({'data': data, 'preview': preview, 'reload': reload})

    def get_form_template_names(self, prefix=None, preview=False):

        template_syntax = self.form_template_name_syntax if not preview else \
            self.preview_template_name_syntax

        template_names = [template_syntax.format(prefix=prefix), ]

        if not preview and self.form_default_template:
            template_names.append(self.form_default_template)
        return template_names

    def get_form_context(self, form=None):
        return {'form': form}

    def get_preview_context(self):
        return {}

    def get(self, *args, **kwargs):
        preview = self.request.GET.get('preview', None)
        if preview:
            return self.render_to_response(self.get_context_data(), preview=True)
        return super(JsonMultiModelFormView, self).get(*args, **kwargs)

    @transaction.atomic()
    def form_valid(self):
        self.save_forms()
        return self.render_to_response(self.get_context_data(), preview=True)

    def form_invalid(self):
        super(JsonMultiModelFormView, self).form_invalid()
        return self.render_to_response(self.get_context_data())


class ExportView(TemplateView):

    # context key name for queryset
    context_queryset_keys = ['initiatives', 'obj_list']

    def get_filename(self):
        """ filename without extension """
        return 'export'

    def get_response_params(self):
        filename = self.get_filename()
        csv = {
            'content_type': 'text/csv',
            'content_disposition': 'attachment; filename="{}.xlsx"'.format(filename)
        }
        xlsx = {
            'content_type': 'application/vnd.openxmlformats-officedocument.'
                            'spreadsheetml.sheet',
            'content_disposition': 'attachment; filename="{}.xlsx"'.format(filename)}
        return {
            'xlsx': xlsx,
            'csv': csv,
        }

    def get(self, request, *args, **kwargs):
        if 'export' in request.GET:
            response_params = self.get_response_params()
            output_type = request.GET['export']
            context = self.get_context_data()
            qs = []
            for qs_key in self.context_queryset_keys:
                if context.get(qs_key, None):
                    qs = context[qs_key]
                    break

            response = HttpResponse(
                getattr(self.get_resource(qs), output_type),
                content_type=response_params[output_type]['content_type'])
            response['Content-Disposition'] = \
                response_params[output_type]['content_disposition']
            return response
        return super(ExportView, self).get(request, *args, **kwargs)

    def get_resource(self, qs):
        return InitiativeResource().export(qs)


@requires_csrf_token
def page_not_found(request, template_name='nuka/errors/404.html'):
    context = {'request_path': request.path}
    template = loader.get_template(template_name)
    body = template.render(context, request)
    content_type = None
    return http.HttpResponseNotFound(body, content_type=content_type)
