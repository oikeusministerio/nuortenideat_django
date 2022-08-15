# coding=utf-8

from __future__ import unicode_literals

from django.conf.urls import patterns, url

from content.models import Initiative
from content.perms import CanPublishIdea

from libs.djcontrib.conf.urls import decorated_patterns
from libs.djcontrib.utils.decorators import combo
from libs.permitter.decorators import check_perm
from libs.djcontrib.utils.decorators import obj_by_pk
from nuka.decorators import legacy_json_plaintext

from nuka.perms import IsAuthenticated, IsModerator

from . import views, forms
from .models import Organization
from .perms import CanViewOrganization, CanEditOrganization
from slug.decorators import slug_to_object
from slug.views import SlugRedirect

org_by_pk = obj_by_pk(Organization)
obj_by_slug = slug_to_object(Organization)

# TODO: DRY against content.urls, generic edit&detail view?

ORGANIZATION_FRAGMENT_URLS = (
    # (url part, template name/url name part, form_class)
    # (r'kuva',           'picture',          forms.EditOrganizationPictureForm),
    (r'kuvaus',         'description',      forms.EditOrganizationDescriptionForm),
    (r'yhteyshenkilot', 'admins',           forms.EditOrganizationAdminsForm),
    (r'nimi',           'name',             forms.EditOrganizationNameForm),
    (r'tyyppi',         'type',             forms.EditOrganizationTypeForm),
)

partial_detail_urls = [
    url(r'(?P<pk>\d+)/nayta/%s/$' % u[0],
        views.OrganizationPartialDetailView.as_view(),
        name='organization_detail_%s' % u[1],
        kwargs={'template_name': 'organization/organization_detail_%s.html' % u[1]}
    ) for u in ORGANIZATION_FRAGMENT_URLS
]

partial_edit_patterns = [
    url(r'(?P<pk>\d+)/muokkaa/%s/$' % u[0],
        legacy_json_plaintext(views.OrganizationPartialEditView.as_view()),
        name='edit_organization_%s' % u[1],
        kwargs={'template_name': 'organization/organization_edit_%s_form.html' % u[1],
                'form_class': u[2], 'fragment': u[1]}
    ) for u in ORGANIZATION_FRAGMENT_URLS
]

urlpatterns = patterns(
    '',
    url(r'^$', views.OrganizationListView.as_view(), name='list'),
    url(r'uusi/$', check_perm(IsAuthenticated)(views.CreateOrganizationView.as_view()),
        name='create'),
    url(r'^(?P<pk>\d+)/arkistoi/',
        org_by_pk(check_perm(IsModerator)(views.OrganizationArchiveView.as_view())),
        name='archive'),
    url(r'^(?P<pk>\d+)/piilota/',
        org_by_pk(
            check_perm(IsModerator)(views.OrganizationSetActiveView.as_view(active=False))
        ),
        name='deactivate'),
    url(r'^(?P<pk>\d+)/aktivoi/',
        org_by_pk(
            check_perm(IsModerator)(views.OrganizationSetActiveView.as_view(active=True))
        ),
        name='activate'),
) + decorated_patterns('', combo(org_by_pk, check_perm(CanViewOrganization)),
    url(r'^(?P<pk>\d+)/$', SlugRedirect.as_view(model=Organization, permanent=False),
        name='detail_pk'),
    url(r'^(?P<pk>\d+)/lista/$', views.OrganizationIdeaList.as_view(), name='idea_list'),
    *partial_detail_urls
) + decorated_patterns('', combo(obj_by_slug, check_perm(CanViewOrganization)),
    url(r'^(?P<slug>[\w-]+)/$', views.OrganizationDetailView.as_view(), name='detail'),
) + decorated_patterns('', combo(org_by_pk, check_perm(CanEditOrganization)),
    url(r'^(?P<pk>\d+)/kuva/$', views.PictureView.as_view(),
        name='picture'),
    url(r'^(?P<pk>\d+)/kuva/muokkaa/$',
        legacy_json_plaintext(views.EditPictureView.as_view()),
        name='edit_picture'),
    url(r'^(?P<pk>\d+)/kuva/rajaa/$',
        views.CropProfilePictureView.as_view(), name='crop_picture'),
    url(r'^(?P<pk>\d+)/kuva/poista/$',
        views.DeletePictureView.as_view(),
        name='delete_picture'),
    *partial_edit_patterns
)
