# coding=utf-8

from __future__ import unicode_literals

from functools import wraps
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from content.models import Idea, IdeaSurvey
from openapi.serializers import PaginatedCommentSerializer, PaginatedIdeaSerializer, \
    PaginatedSurveySerializer, PaginatedQuestionSerializer
from organization.models import Organization
from survey.models import Survey
from tagging.models import Tag

from . import serializers


def with_serializer(serializer_class):
    def _deco(method):
        @wraps(method)
        def _inner(self, *args, **kwargs):
            old_serializer_class = self.serializer_class
            try:
                self.serializer_class = serializer_class
                return method(self, *args, **kwargs)
            finally:
                self.serializer_class = old_serializer_class
        return _inner
    return _deco


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.normal()
    serializer_class = serializers.OrganizationSerializer
    paginate_by = 50

    @with_serializer(serializers.OrganizationDetailSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        Returns details about the organization.
        ---
        response_serializer: ..serializers.OrganizationDetailSerializer
        """
        return super(OrganizationViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Returns a paginated list of all active organizations.
        ---
        response_serializer: ..serializers.PaginatedOrganizationSerializer
        """
        return super(OrganizationViewSet, self).list(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='ideas')
    def list_ideas(self, request, pk=None):
        """
        Returns a paginated list of ideas targeting the organization.
        ---
        response_serializer: ..serializers.PaginatedIdeaSerializer
        """
        org = get_object_or_404(Organization, pk=pk)
        ideas = Idea.objects.filter(visibility=Idea.VISIBILITY_PUBLIC,
                                    target_organizations__pk=org.pk)\
                            .order_by('-published')
        page = self.paginate_queryset(ideas)
        context = self.get_serializer_context()
        serializer = PaginatedIdeaSerializer(instance=page, context=context)
        return Response(serializer.data)


class IdeaViewSet(viewsets.ReadOnlyModelViewSet):
    paginate_by = 50
    max_paginate_by = 50

    queryset = Idea.objects\
        .filter(visibility=Idea.VISIBILITY_PUBLIC)\
        .order_by('-published')
    serializer_class = serializers.IdeaSerializer

    def list(self, request, *args, **kwargs):
        """
        Returns a paginated list of all public ideas.

        The ideas are sorted from newest to oldest.
        ---
        serializer: ..serializers.PaginatedIdeaSerializer
        """

        return super(IdeaViewSet, self).list(request, *args, **kwargs)

    @with_serializer(serializers.IdeaDetailSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        Returns details about the idea.
        ---
        response_serializer: ..serializers.IdeaDetailSerializer
        """
        return super(IdeaViewSet, self).retrieve(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='comments')
    def list_comments(self, request, pk=None):
        """
        Returns a paginated list of the idea's public comments.
        ---
        response_serializer: ..serializers.PaginatedCommentSerializer
        """
        idea = get_object_or_404(Idea.objects.filter(visibility=Idea.VISIBILITY_PUBLIC),
                                 pk=pk)
        comments = idea.public_comments().public().order_by('-pk')
        page = self.paginate_queryset(comments)
        context = self.get_serializer_context()
        serializer = PaginatedCommentSerializer(instance=page, context=context)
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path='surveys')
    def list_surveys(self, request, pk=None):
        """
        Returns a paginated list of surveys associated with the idea.
        ---
        response_serializer: ..serializers.PaginatedSurveySerializer
        """
        idea = get_object_or_404(Idea.objects.filter(
            visibility=Idea.VISIBILITY_PUBLIC), pk=pk)
        ct = ContentType.objects.get_for_model(Survey)
        pd_surveys = IdeaSurvey.objects.filter(idea__pk=idea.pk, content_type_id=ct).\
            exclude(status=IdeaSurvey.STATUS_DRAFT)
        page = self.paginate_queryset(pd_surveys)
        context = self.get_serializer_context()
        serializer = PaginatedSurveySerializer(instance=page, context=context)
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer

    paginate_by = 50
    max_paginate_by = 50

    def list(self, request, *args, **kwargs):
        """
        Returns a paginated list of all tags.
        ---
        response_serializer: ..serializers.PaginatedTagSerializer
        """
        return super(TagViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Returns basic details about the tag.
        """
        return super(TagViewSet, self).retrieve(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='ideas')
    def list_ideas(self, request, pk=None):
        """
        Returns a paginated list of ideas associated with the tag.
        ---
        response_serializer: ..serializers.PaginatedIdeaSerializer
        """
        tag = get_object_or_404(Tag, pk=pk)
        ideas = Idea.objects.filter(visibility=Idea.VISIBILITY_PUBLIC, tags__pk=tag.pk)\
                            .order_by('-published')
        page = self.paginate_queryset(ideas)
        context = self.get_serializer_context()
        serializer = PaginatedIdeaSerializer(instance=page, context=context)
        return Response(serializer.data)


class SurveyViewSet(viewsets.ReadOnlyModelViewSet):
    paginate_by = 50
    max_paginate_by = 50
    queryset = IdeaSurvey.objects.filter(
        idea__visibility=Idea.VISIBILITY_PUBLIC,
        content_type_id=ContentType.objects.get_for_model(Survey)
    ).exclude(status=IdeaSurvey.STATUS_DRAFT)
    serializer_class = serializers.SurveySerializer

    def list(self, request, *args, **kwargs):
        """
        Returns a paginated list of all public surveys.

        Surveys are sorted from newest to oldest.
        ---
        serializer: ..serializers.SurveyDetailSerializer
        """

        return super(SurveyViewSet, self).list(request, *args, **kwargs)

    @with_serializer(serializers.SurveyDetailSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        Returns details about the Survey.
        ---
        response_serializer: ..serializers.SurveyDetailSerializer
        """
        return super(SurveyViewSet, self).retrieve(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='questions')
    def list_questions(self, request, pk=None):
        """
        Returns a paginated list of questions in survey.
        ---
        response_serializer: ..serializers.PaginatedQuestionSerializer
        """
        survey = get_object_or_404(Survey, pk=pk)
        questions = survey.elements.questions()
        page = self.paginate_queryset(questions)
        context = self.get_serializer_context()
        serializer = PaginatedQuestionSerializer(instance=page, context=context)
        return Response(serializer.data)