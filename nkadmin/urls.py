# coding=utf-8

from __future__ import unicode_literals

from django.conf.urls import url

from libs.djcontrib.conf.urls import decorated_patterns
from libs.djcontrib.utils.decorators import combo
from libs.permitter.decorators import check_perm
from libs.djcontrib.utils.decorators import obj_by_pk

from account.models import User

from . import views
from .perms import CanAccessAdminPanel, CanEditUser


urlpatterns = decorated_patterns('', check_perm(CanAccessAdminPanel),
    url(r'^moderointi/$', views.ModerationQueueView.as_view(), name='moderation_queue'),
    url(r'^organisaatiot/$', views.ModerationOrganizationQueueView.as_view(),
        name='moderation_organization_queue'),
    url(r'^kayttajat/$', views.UsersView.as_view(), name='users'),
    url(r'^kayttajat/(?P<filter>\w+)/$', views.UsersView.as_view(), name='users'),
    url(r'^raportit/$', views.ReportsView.as_view(), name='reports'),
    url(r'^raportit/ideat-aiheittain/$', views.IdeasByTagReportView.as_view(),
        name='ideas_by_tags'),
    url(r'^raportit/kayttaja-aktiivisuus/$', views.UserActivityReportView.as_view(),
        name='user_activity'),
    url(r'^moderointi/paivita-oikeudet/$', views.UpdateModeratorRightsView.as_view(),
        name='moderator_rights'),
)

urlpatterns += decorated_patterns(
    '',
    combo(obj_by_pk(User), check_perm(CanEditUser)),
    url(
        r'^kayttajat/(?P<pk>\d+)/muokkaa/$',
        views.EditUserView.as_view(),
        name='users_edit'
    ),
    url(
        r'^kayttajat/(?P<pk>\d+)/vaihda_salasana/$',
        views.SetPasswordView.as_view(),
        name='change_password'
    )
)