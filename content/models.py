# coding=utf-8

from __future__ import unicode_literals
from django.template.defaultfilters import date
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _, ugettext
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey

from imagekit.models.fields import ImageSpecField, ProcessedImageField
from kombu.utils import uuid4
from pilkit.processors.resize import ResizeToFit, Resize
from polymorphic.polymorphic_model import PolymorphicModel
from model_utils import FieldTracker
from actions.signals import action_performed
from kuaapi.utils import get_kua_and_idea_status_map

from libs.attachtor import signals as attachtor

from kuaapi.models import KuaInitiativeStatus, KuaInitiative
from account.models import User
from nuka.models import MultilingualRedactorField, MultilingualTextField
from nuka.utils import strip_tags
from organization.models import Organization
from actions.models import ActionGeneratingModelMixin


def _idea_main_pic_path(obj, name):
    return 'initiative/%d/pictures/%s.jpg' % (obj.pk, uuid4().hex)


class ModeratedPolymorphicModelMixIn(object):
    """Prevent "AttributeError" can't set attribute
    @ moderation.register.ModerationManager._copy_model_instance"""

    def __init__(self, *args, **kwargs):
        if kwargs.get('initiative_ptr', None) is not None:
            kwargs['initiative_ptr_id'] = kwargs.pop('initiative_ptr').pk
        super(ModeratedPolymorphicModelMixIn, self).__init__(*args, **kwargs)


@python_2_unicode_compatible
class Initiative(PolymorphicModel, ActionGeneratingModelMixin):
    VISIBILITY_DRAFT = 1
    VISIBILITY_ARCHIVED = 8
    VISIBILITY_PUBLIC = 10
    VISIBILITIES = (
        (VISIBILITY_DRAFT,    '',         _("Luonnos")),
        (VISIBILITY_PUBLIC,   '',         _("Julkinen")),
        (VISIBILITY_ARCHIVED, 'archived', _("Arkistoitu")),
    )
    VISIBILITY_CHOICES = [(s[0], s[2]) for s in VISIBILITIES]

    INTERACTION_EVERYONE = 1
    INTERACTION_REGISTERED_USERS = 2
    INTERACTION_CHOICES = (
        (INTERACTION_EVERYONE,          _("Kaikki")),
        (INTERACTION_REGISTERED_USERS,  _("Rekisteröityneet käyttäjät")),
    )

    title = MultilingualTextField(_("otsikko"), max_length=255, simultaneous_edit=True)
    description = MultilingualRedactorField(_("kuvaus"), blank=True)

    initiator_organization = models.ForeignKey('organization.Organization', null=True,
                                               on_delete=models.CASCADE,
                                               related_name='initiation')
    owners = models.ManyToManyField('account.User', related_name='initiatives')
    # creator == User who initially created the object, not displayed in the UI
    creator = models.ForeignKey('account.User', null=True, on_delete=models.SET_NULL)
    target_organizations = models.ManyToManyField('organization.Organization',
                                                  #through='InitiativeTarget',
                                                  related_name='targeted_initiatives',
                                                  verbose_name=_("kohde organisaatiot"))

    tags = models.ManyToManyField('tagging.Tag', verbose_name=_("aiheet"))
    visibility = models.SmallIntegerField(_("näkyvyys"), choices=VISIBILITY_CHOICES,
                                          default=VISIBILITY_DRAFT)
    interaction = models.SmallIntegerField(_("Kuka saa kannattaa ja kommentoida?"),
                                           choices=INTERACTION_CHOICES,
                                           default=INTERACTION_EVERYONE)
    premoderation = models.BooleanField(_("kommenttien esimoderointi"), default=False)
    commenting_closed = models.BooleanField(_("kommentointi suljettu"), default=False)
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now=True)
    published = models.DateTimeField(null=True, default=None, blank=True)
    archived = models.DateTimeField(null=True, default=None, blank=True)

    comments = GenericRelation('nkcomments.CustomComment',
                               object_id_field='object_pk')

    field_tracker = FieldTracker(fields=['premoderation', 'commenting_closed'])

    # action processing
    connect_post_save = False

    def public_comments(self):
        if self.premoderation is True:
            qs = self.comments.filter(is_public=True)
        else:
            qs = self.comments.all()
        #qs = qs.prefetch_related('flags', 'user__organizations')
        return qs

    def description_plaintext(self):
        # @attention: extra string conversion to get description for active language
        return strip_tags('%s' % self.description)

    def is_public(self):
        return self.visibility in (self.VISIBILITY_PUBLIC,
                                   self.VISIBILITY_ARCHIVED)

    def is_voteable(self):
        return False

    def comments_are_voteable(self):
        return self.visibility == self.VISIBILITY_PUBLIC

    def is_archived(self):
        return self.visibility == self.VISIBILITY_ARCHIVED

    @cached_property
    def target_municipality(self):
        """Returns Initiative's target organization whose type is TYPE_MUNICIPALITY,
        if the initiative targets exactly one municipality-Organization. Otherwise
        returns None."""
        municipalities = self.target_organizations\
                             .filter(type=Organization.TYPE_MUNICIPALITY)
        if len(municipalities) == 1:
            return municipalities[0]
        return None

    @cached_property
    def owner_ids(self):
        if self.initiator_organization_id is not None:
            return self.initiator_organization.admins.values_list('pk', flat=True)
        return self.owners.values_list('pk', flat=True)

    def owner_names(self):
        users = User.objects.filter(id__in=self.owner_ids).order_by('id')
        return [u.get_full_name() for u in users]

    def owner_emails(self):
        users = User.objects.filter(id__in=self.owner_ids).order_by('id')
        return [u.email for u in users]

    @cached_property
    def target_organization_ids(self):
        return list(self.target_organizations.values_list('pk', flat=True))

    @cached_property
    def target_organization_admin_ids(self):
        return list(set(User.organizations.through.objects.filter(
            organization_id__in=self.target_organization_ids
        ).values_list('user_id', flat=True)))

    def get_target_organization_email_list(self):
        email_list = []
        for o in self.target_organizations.all():
            email_list.extend(o.get_admins_emails_list())
        return email_list

    def organization_initiated(self):
        if self.initiator_organization is None:
            return False
        else:
            return True

    @property
    def is_locked(self):
        from nkcomments.models import CustomComment
        from nkvote.models import Vote, Answer
        ct = ContentType.objects.get_for_model(self)
        if CustomComment.objects.filter(content_type=ct, object_pk=self.id).count():
            return True
        if Vote.objects.filter(content_object=self).count():
            return True
        if Answer.objects.filter(gallup__idea=self).count():
            return True
        return False

    def check_commenting_options_change(self):
        changed_fields = self.field_tracker.changed()
        fields = ['premoderation', 'commenting_closed']
        for field_name in fields:
            if field_name in changed_fields:
                if getattr(self, field_name) is not changed_fields[field_name]:
                    return True
        return False

    # action processing
    def action_kwargs_on_create(self):
        return {'actor': self.creator}

    def fill_notification_recipients(self, action):

        for u in self.owners.all():
            action.add_notification_recipients(action.ROLE_CONTENT_OWNER, u)

        added_admins = []
        for org in self.target_organizations.all():
            for u in org.admins.all():
                added_admins.append(u)
                action.add_notification_recipients(action.ROLE_ORGANIZATION_CONTACT, u)

        if self.initiator_organization:
            for u in self.initiator_organization.admins.all():
                if u not in added_admins:
                    action.add_notification_recipients(
                        action.ROLE_ORGANIZATION_CONTACT, u)

    def fill_anonymous_notification_recipients(self, action):
        pass

    def __str__(self):
        return '%s' % self.title


class ResizeToMinimumDimensions(object):
    def __init__(self, width=None, height=None):
        self.width, self.height = width, height

    def process(self, img):
        cur_width, cur_height = img.size
        if self.width is not None and self.height is not None:
            ratio = max(float(self.width) / cur_width,
                        float(self.height) / cur_height)
        else:
            if self.width is None:
                ratio = float(self.height) / cur_height
            else:
                ratio = float(self.width) / cur_width
        new_dimensions = (int(round(cur_width * ratio)),
                          int(round(cur_height * ratio)))
        img = Resize(new_dimensions[0], new_dimensions[1], upscale=True).process(img)
        return img


def _is_dupe(item, dupes):
    if item in dupes:
        return True
    dupes.add(item)
    return False


class Idea(ModeratedPolymorphicModelMixIn, Initiative):
    STATUS_DRAFT = 0
    STATUS_PUBLISHED = 3
    STATUS_TRANSFERRED = 6
    STATUS_DECISION_GIVEN = 9
    STATUSES = (
        (STATUS_DRAFT,          'created',          _("Luonnos")),
        (STATUS_PUBLISHED,      'published',        _("Julkaistu")),
        (STATUS_TRANSFERRED,    'transferred',      _("Viety eteenpäin")),
        (STATUS_DECISION_GIVEN, 'decision_given',   _("Vastaus annettu")),
    )
    STATUS_CHOICES = [(s[0], s[2]) for s in STATUSES]

    # Large picture, to be used as a source for pictures actually displayed on the site
    picture = ProcessedImageField(upload_to=_idea_main_pic_path,
        processors=[ResizeToFit(width=1280, height=1280*4, upscale=False)],
        format='JPEG', options={'quality': 90}
    )

    # Medium picture, to be displayed on the Idea page, with some effort to make it
    # fixed width
    picture_main = ImageSpecField(source='picture',
                                  processors=[
                                      ResizeToMinimumDimensions(width=710),
                                      ResizeToFit(width=710, height=4*710),
                                  ], format='JPEG', options={'quality': 70})

    # Narrow picture, to be displayed on grids with multiple Ideas, cropping allowed
    picture_narrow = ImageSpecField(source='picture',
                                    processors=[ResizeToMinimumDimensions(width=350),
                                                ResizeToFit(width=350, height=4*350)],
                                    format='JPEG', options={'quality': 70})

    picture_alt_text = models.CharField(_("Mitä kuvassa on? (kuvaus suositeltava)"),
                                        max_length=255,
                                        default=None,
                                        null=True)

    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_DRAFT)
    auto_transfer_at = models.DateField(_("Idean vienti eteenpäin automaattisesti"),
                                        null=True, default=None, blank=True)
    transferred = models.DateTimeField(null=True, default=None, blank=True)
    decision_given = models.DateTimeField(null=True, default=None, blank=True)

    votes = GenericRelation("nkvote.Vote", related_query_name="ideas")
    search_text = models.TextField(default=None, null=True)
    status_tracker = FieldTracker(fields=['status'])

    def get_absolute_url(self):
        return reverse('content:idea_detail', kwargs={'initiative_id': self.pk})

    def is_voteable(self):
        return True

    @property
    def popularity(self):
        return self.comments.all().count() + self.votes.all().count()

    def is_idea(self):
        return True

    def is_voteable(self):
        return self.status == self.STATUS_PUBLISHED and not self.is_archived()

    def status_or_visibility(self):
        if self.visibility == self.VISIBILITY_ARCHIVED:
            return self.get_visibility_display()
        return self.get_status_display()

    def html_allowed(self):
        return True

    def get_status_values(self, statuses, status, add_status_value=False):
        if add_status_value:
            return tuple((status, getattr(self, statuses[status][0]),
                         statuses[status][1], ))
        return tuple((getattr(self, statuses[status][0]), statuses[status][1], ))

    def get_kua_statuses_to_status_list(self, add_status_value=False):
        try:
            kuas, dupes = [], set()
            for s in self.kua_initiative.statuses.all():
                msg = s.get_friendly_status_message()
                if msg is not None and not _is_dupe(msg, dupes):
                    if add_status_value:
                        idea_status = get_kua_and_idea_status_map(self,
                                                                  kua_status=s.status)
                        kuas.append((idea_status, s.created, msg, ))
                    else:
                        kuas.append((s.created, msg, ))
            return kuas
        except KuaInitiative.DoesNotExist:
            return []

    def get_status_list(self, add_status_value=False):
        statuses = dict([(s[0], (s[1], s[2])) for s in self.STATUSES])
        ret = []
        if self.status == self.STATUS_DRAFT:
            ret.append(self.get_status_values(statuses, self.STATUS_DRAFT,
                                              add_status_value))
        else:
            ret.append(self.get_status_values(statuses, self.STATUS_PUBLISHED,
                                              add_status_value))
            kua_status_list = self.get_kua_statuses_to_status_list(add_status_value)
            if kua_status_list:
                ret.extend(kua_status_list)
            elif self.status >= self.STATUS_TRANSFERRED:
                ret.append(self.get_status_values(statuses, self.STATUS_TRANSFERRED,
                                                  add_status_value))

            if self.status == self.STATUS_DECISION_GIVEN:
                ret.append(self.get_status_values(statuses, self.STATUS_DECISION_GIVEN,
                                                  add_status_value))
            if self.visibility == self.VISIBILITY_ARCHIVED:
                visibilities = dict([(s[0], (s[1], s[2])) for s in self.VISIBILITIES])
                ret.append(self.get_status_values(visibilities, self.VISIBILITY_ARCHIVED,
                                                  add_status_value))
        return ret

    def transfer_idea(self, create_detail=True):
        self.status = self.STATUS_TRANSFERRED
        self.transferred = timezone.now()
        self.save()

        if create_detail:
            detail = []
            for o in self.target_organizations.all():
                detail.append("{} / {}".format(o.name, o.admins_str()))

            self.details.create(
                detail="\n".join(detail),
                type=AdditionalDetail.TYPE_TRANSFERRED
            )
        return self

    def status_complete(self, unnecessary_dates=True):
        status = self.get_status_list().pop()
        no_dates = [Idea.VISIBILITY_ARCHIVED]
        if not unnecessary_dates and self.visibility in no_dates:
            return status[1]
        else:
            status_date = date(status[0], 'SHORT_DATE_FORMAT')
            return "{}: {}".format(status[1], status_date)

    def status_complete_fixed_dates(self):
        return self.status_complete(unnecessary_dates=False)

    ACTION_SUB_TYPE_IDEA_PUBLISHED = 'idea-published'
    ACTION_SUB_TYPE_STATUS_UPDATED = 'status-updated'
    ACTION_SUB_TYPE_STATUS_UPDATED_AFTER_PUBLISH = 'status-updated-after-publish'

    def check_status_change(self):
        changed_fields = self.status_tracker.changed()
        if 'status' in changed_fields:
            if self.status is not changed_fields['status']:
                return True
        return False

    def get_subtypes(self):
        subtypes = []
        if self.check_status_change():
            subtypes.append(Idea.ACTION_SUB_TYPE_STATUS_UPDATED)
            if self.status == Idea.STATUS_PUBLISHED:
                subtypes.append(Idea.ACTION_SUB_TYPE_IDEA_PUBLISHED)
            if self.status > Idea.STATUS_PUBLISHED:
                subtypes.append(Idea.ACTION_SUB_TYPE_STATUS_UPDATED_AFTER_PUBLISH)
        return subtypes

    def create_updated_action(self):
        return self.check_status_change()

    def action_kwargs_on_update(self):
        return {'actor': None, 'subtype': self.get_subtypes()}  # TODO: save modifier

    def count_survey_submissions(self):
        count = 0
        for s in self.idea_surveys.all():
            count += s.count_submissions()
        return count

    def close_surveys(self):
        for s in self.idea_surveys.all():
            s.close()


@receiver(post_save, sender=Idea)
def create_action_on_update(instance=None, created=False, **kwargs):
    if not created and instance.check_status_change():
        action_performed.send(sender=instance, created=created)


class IdeaSurveyQuerySet(models.QuerySet):
    def drafts(self):
        id_list = [x.pk for x in self.all() if x.is_draft()]
        return self.filter(id__in=id_list)


@python_2_unicode_compatible
class IdeaSurvey(models.Model):
    STATUS_DRAFT = 1
    STATUS_OPEN = 5
    STATUS_CLOSED = 10

    INTERACTION_EVERYONE = 1
    INTERACTION_REGISTERED_USERS = 2
    INTERACTION_CHOICES = (
        (INTERACTION_EVERYONE,          _("Kaikki")),
        (INTERACTION_REGISTERED_USERS,  _("Rekisteröityneet käyttäjät")),
    )

    ANSWER_MODE_NORMAL = 0
    ANSWER_MODE_ANONYMOUS_UNLIMITED = 1
    ANSWER_MODE_CHOICES = (
        (ANSWER_MODE_NORMAL, _("Yksi vastaus osallistujaa kohden")),
        (ANSWER_MODE_ANONYMOUS_UNLIMITED, _("Rajattomat vastaukset kirjautumattomille "
                                            "käyttäjille")),
    )

    idea = models.ForeignKey(Idea, related_name='idea_surveys')
    content_type = models.ForeignKey(ContentType, default=None)
    object_id = models.PositiveIntegerField(default=None)
    content_object = GenericForeignKey()
    status = models.SmallIntegerField(default=STATUS_DRAFT)
    created = models.DateTimeField(auto_now_add=True)
    opened = models.DateTimeField(null=True)
    closed = models.DateTimeField(null=True)
    interaction = models.SmallIntegerField(_("Kuka saa vastata kyselyyn?"),
                                           choices=INTERACTION_CHOICES,
                                           default=INTERACTION_EVERYONE)
    title = MultilingualTextField(_("otsikko"), max_length=255, simultaneous_edit=True)
    answer_mode = models.SmallIntegerField(_("Vastaamisen asetukset"),
                                           choices=ANSWER_MODE_CHOICES,
                                           default=ANSWER_MODE_NORMAL)

    objects = IdeaSurveyQuerySet.as_manager()

    def is_open(self):
        return self.status == self.STATUS_OPEN

    def is_draft(self):
        return self.status == self.STATUS_DRAFT

    def is_closed(self):
        return self.status == self.STATUS_CLOSED

    def get_absolute_url(self):
        idea_url = self.idea.get_absolute_url()
        return "{}#survey-{}".format(idea_url, self.pk)

    def count_submissions(self):
        return self.content_object.submissions.count()

    def close(self):
        self.status = self.STATUS_CLOSED
        self.closed = timezone.now()
        self.save()

    def __str__(self):
        title = self.title.__get_any_value__()
        return title if title else ugettext("Kysely")


class Question(ModeratedPolymorphicModelMixIn, Initiative):

    user_name = models.CharField(max_length=100)
    user_email = models.EmailField(max_length=254, unique=False,
                                   blank=True, default=None, null=True)

    @property
    def organization(self):
        return self.target_organizations.first()

    @property
    def owner(self):
        return self.owners.first()

    def get_absolute_url(self):
        return reverse('content:question_detail', kwargs={'initiative_id': self.pk})

    def is_votable(self):
        return False

    def is_idea(self):
        return False

    def html_allowed(self):
        return self.creator_id is not None

    # action generating
    def fill_anonymous_notification_recipients(self, action):
        if self.user_email:
            action.add_anonymous_notification_recipients(action.ROLE_CONTENT_OWNER, {
                'user_name': self.user_name,
                'user_email': self.user_email
            })


class AdditionalDetail(models.Model):

    TYPE_NONE = 0
    TYPE_DECISION = 1
    TYPE_TRANSFERRED = 2
    TYPES = (
        (TYPE_NONE,         '',     _("lisätieto")),
        (TYPE_DECISION,     '#c3e2a6',  _("VASTAUS")),
        (TYPE_TRANSFERRED,  '#cfcfcf', _("Viety eteenpäin")),
    )
    TYPE_CHOICES = [(s[0], s[2]) for s in TYPES]

    idea = models.ForeignKey(Idea, related_name='details')
    detail = MultilingualRedactorField(_("lisätieto"))
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now=True)
    type = models.SmallIntegerField(choices=TYPE_CHOICES, default=TYPE_NONE)

    def get_bgcolor(self):
        return filter(lambda x: x[0] == self.type, self.TYPES)[0][1]

    class Meta:
        ordering = ['created', 'pk', ]


@receiver(post_save, sender=KuaInitiativeStatus)
def update_decision_given_timestamp(instance=None, created=False, **kwargs):
    if created and instance.status == KuaInitiativeStatus.STATUS_DECISION_GIVEN:
        idea = instance.kua_initiative.idea
        if idea.decision_given is None:
            idea.status = Idea.STATUS_DECISION_GIVEN
            idea.decision_given = timezone.now()
            idea.save()

@receiver(pre_save, sender=Idea)
def update_search_text(instance=None, **kwargs):
    instance.search_text = ' '.join(map(strip_tags,
                                        instance.title.values() +
                                        instance.description.values()))

@receiver(pre_save, sender=Idea)
def status_field_checker(instance=None, **kwargs):
    instance.__status = instance.status


# Manually register derived polymorphic model RedactorAttachtorFields for attachment
# maintanence, because model signals are usually sent as the derived class and not the
# parent class containing the field (which is autoregistered)
attachtor.register(Idea, 'description')
attachtor.register(Question, 'description')

