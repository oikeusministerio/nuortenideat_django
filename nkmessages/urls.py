# coding=utf-8

from __future__ import unicode_literals

from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(r'^$', views.FeedbackView.as_view(), name="feedback")
)