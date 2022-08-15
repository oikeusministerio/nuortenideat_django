# coding=utf-8

from __future__ import unicode_literals

from datetime import datetime
from dateutil.relativedelta import relativedelta
from django import forms
from django.template.defaultfilters import date as date_filter
from django.conf import settings
from django.db.models.aggregates import Sum, Count
from django.db.models import Q
from django.forms.models import ModelForm
from django.forms.widgets import RadioSelect
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from file_resubmit.admin import AdminResubmitImageWidget
from nocaptcha_recaptcha import NoReCaptchaField

from libs.attachtor.forms.fields import RedactorAttachtorField
from libs.attachtor.forms.forms import RedactorAttachtorFormMixIn, FileUploadForm
from libs.attachtor.models.models import Upload
from libs.fimunicipality.models import Municipality

from account.models import User
from nuka.forms.forms import HiddenLabelMixIn, PopoverFormMixin, StripEmojisMixin, \
    WordSearchMixin
from nuka.forms.fields import ModelMultipleChoiceField, SaferFileField, \
    MultilingualRedactorField
from nuka.forms.widgets import Select2Multiple, AutoSubmitButtonSelect, NukaDateTimePicker
from nuka.utils import send_email, strip_tags, strip_emojis
from organization.models import Organization
from tagging.models import Tag

from .models import IdeaSurvey
from .perms import CanChangeIdeaSettings, CanEditInitiative
from .models import Idea, AdditionalDetail, Question, Initiative

MAX_DAYS_TO_IDEA_AUTO_TRANSFER = 8 * 7


def get_organization_choices(user=None, unknown=False):
    def create_choices(qs):
        return tuple([(o.pk, o) for o in qs.all()])

    qs = Organization.objects.active()

    if not unknown:
        qs = qs.real()

    if user:
        priority_organizations = qs.filter(
            municipalities__id=user.settings.municipality_id)
        other_organizations = qs.exclude(
            pk__in=priority_organizations.values_list('pk', flat=True))

        if priority_organizations:
            choices = ((_("Organisaatiot omassa kunnassa"),
                        create_choices(priority_organizations),),
                       (_("Muut organisaatiot"),
                        create_choices(other_organizations),),
                       )
            return choices
    return create_choices(qs)


class CreateIdeaForm(StripEmojisMixin, RedactorAttachtorFormMixIn, PopoverFormMixin,
                     ModelForm):
    TARGET_TYPE_ORGANIZATION = -1
    TARGET_TYPE_NATION = Organization.TYPE_NATION
    TARGET_TYPE_UNKNOWN = Organization.TYPE_UNKNOWN

    WRITE_AS_USER = 0
    WRITE_AS_ORGANIZATION = 1

    strip_emoji_fields = ['title', 'description']

    picture = forms.ImageField(label=_("Otsikkokuva"), widget=AdminResubmitImageWidget,
                               required=False)
    picture_alt_text = forms.CharField(label=_("Mitä kuvassa on? (kuvaus suositeltava)"),
                                       required=False)

    description = MultilingualRedactorField(label=_("Idean sisältö"), required=True)

    write_as = forms.ChoiceField(
        label=_("Kirjoitetaanko idea organisaationa vai käyttäjänä?"),
        widget=RadioSelect,
        choices=(
            (WRITE_AS_USER,          _("Kirjoita käyttäjänä")),
            (WRITE_AS_ORGANIZATION,  _("Kirjoita organisaationa"))
        ),
        initial=WRITE_AS_USER,
        help_text=_(
            "Olet yhteyshenkilönä vähintään yhdessä organisaatiossa, joten "
            "voit valita kirjoittaa idean organisaationa tai tavallisena käyttäjänä."
        )
    )

    owners = ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        label=_("Valitse idean omistajat"),
        help_text=_("Valitse idean muiden omistajien Nuortenideat.fi-käyttäjätunnukset.")
    )

    target_type = forms.ChoiceField(
        label=_("Mitä organisaatioita idea koskee?"), widget=RadioSelect,
        initial=TARGET_TYPE_ORGANIZATION,
        choices=(
            (TARGET_TYPE_ORGANIZATION,  _("Valittuja organisaatioita")),
            (TARGET_TYPE_NATION,        _("Idea koskee koko Suomea")),
            (TARGET_TYPE_UNKNOWN,       _("En osaa sanoa")),
        )
    )
    target_organizations = ModelMultipleChoiceField(
        queryset=Organization.objects.real().active(),
        help_text=_("Valitse organisaatio tai organisaatiot, joihin idea liittyy."),
        label='', required=False
    )
    tags = ModelMultipleChoiceField(label=_("Valitse aiheet"), widget=Select2Multiple,
                                    queryset=Tag.objects.all(), required=False,
                                    help_text=_("Valitse ideaan liittyvät aiheet."))

    def __init__(self, user, *args, **kwargs):
        super(CreateIdeaForm, self).__init__(*args, **kwargs)

        if self.data.get('target_type', None) == self.TARGET_TYPE_ORGANIZATION:
            self.fields['target_organizations'].required = True

        self.fields['target_organizations'].choices = get_organization_choices(user)

        user_organizations = user.organizations.all().active()
        if user_organizations:
            self.fields["initiator_organization"] = forms.ModelChoiceField(
                label=_("Organisaatio, jona idea kirjoitetaan."),
                queryset=user_organizations,
                empty_label=None,
                required=False
            )
        else:
            del self.fields["write_as"]
            del self.fields["initiator_organization"]

    def clean_title(self):
        title_fi = strip_tags(self.cleaned_data["title"]["fi"])
        title_sv = strip_tags(self.cleaned_data["title"]["sv"])
        if title_fi and title_sv:
            cleaned_title_fi = strip_emojis(title_fi)
            cleaned_title_sv = strip_emojis(title_sv)
            if not cleaned_title_fi.isspace() and not cleaned_title_sv.isspace():
                return {"fi": cleaned_title_fi, "sv": cleaned_title_sv}
        elif title_fi:
            cleaned_title_fi = strip_emojis(title_fi)
            if not cleaned_title_fi.isspace():
                return {"fi": cleaned_title_fi, "sv": ''}
        elif title_sv:
            cleaned_title_sv = strip_emojis(title_sv)
            if not cleaned_title_sv.isspace():
                return {"fi": '', "sv": cleaned_title_sv}

    def clean_description(self):
        description_fi = strip_tags(self.cleaned_data["description"]["fi"])
        description_sv = strip_tags(self.cleaned_data["description"]["sv"])
        cleaned_description_fi = strip_emojis(description_fi)
        cleaned_description_sv = strip_emojis(description_sv)

        if not cleaned_description_fi.isspace() or not cleaned_description_sv.isspace():
            return {"fi": cleaned_description_fi, "sv": cleaned_description_sv}

    def clean_picture_alt_text(self):
        alt_text = strip_tags(self.cleaned_data["picture_alt_text"])
        cleaned_alt_text = strip_emojis(alt_text)
        return cleaned_alt_text

    def clean_owners(self):
        """The view should supply initial owners list containing the request.user,
        make sure s/he is still on the list."""
        owners = self.cleaned_data['owners']
        if self.initial['owners'][0] not in owners:
            raise forms.ValidationError(_("Et voi poistaa itseäsi idean omistajista."))
        return owners

    def clean(self):
        cleaned = super(CreateIdeaForm, self).clean()

        if 'target_type' in cleaned:
            target_type = int(cleaned['target_type'])
            if target_type in (self.TARGET_TYPE_UNKNOWN, self.TARGET_TYPE_NATION):
                cleaned['target_organizations'] = [Organization.objects.get(
                    type=target_type
                )]
            elif not cleaned["target_organizations"]:
                self.add_error("target_organizations", _("Tämä kenttä vaaditaan."))

        try:
            if int(cleaned["write_as"]) == self.WRITE_AS_ORGANIZATION:
                cleaned["owners"] = []
            elif int(cleaned["write_as"]) == self.WRITE_AS_USER:
                cleaned["initiator_organization"] = None
        except KeyError:
            pass

        return cleaned

    class Meta:
        model = Idea
        fields = ('title', 'picture', 'picture_alt_text', 'description', 'write_as',
                  'initiator_organization', 'owners', 'target_type',
                  'target_organizations', 'tags', 'interaction', 'commenting_closed')
        widgets = {'interaction': RadioSelect, }
        popovers = {
            'title': _("Anna ideallesi nimi, joka kuvaa sen sisältöä."),
            'picture': _(
                "Lisää halutessasi ideaasi siihen sopiva kuva. Kuva näkyy palvelun "
                "etusivulla ideasi otsikon yläpuolella. Tarkista, että sinulla on "
                "lupa kuvan käyttöön, jos se ei ole omasi."),
            'description': _(
                "Kirjoita tähän kuvaus ideastasi sekä perustelut. Ideassa tulee olla "
                "jokin muutosehdotus, jotta se voidaan viedä eteenpäin käsiteltäväksi. "
                "Voit lisätä mm. kuvia ja linkittää videoita."),
            'owners': _("Jos olet tehnyt idean yhdessä muiden kanssa, voit lisätä myös "
                        "heidät idean omistajiksi kirjoittamalla käyttäjätunnukset "
                        "tähän."),
            'target_type': _("Jos organisaatio löytyy palvelusta, valitse \"Valittuja "
                             "organisaatioita\" ja kirjoita se alla olevaan laatikkoon. "
                             "Jos ideasi on valtakunnallinen, valitse \"Idea koskee "
                             "koko Suomea\". Jos et tiedä, mille organisaatiolle ideasi "
                             "tulisi osoittaa, valitse \"En osaa sanoa\"."),
            'tags': _("Mihin aiheisiin ideasi liittyy? Klikkaa alla olevaa kenttää, "
                      "jolloin vaihtoehdot tulevat näkyviin. Voit valita myös useamman "
                      "aiheen ideallesi."),
        }


class EditIdeaBaseForm(HiddenLabelMixIn, ModelForm):
    pass


class EditInitiativeTitleForm(StripEmojisMixin, EditIdeaBaseForm):
    perm_class = CanEditInitiative
    strip_emoji_fields = ['title']

    class Meta:
        model = Initiative
        fields = ('title', )


class EditInitiativeDescriptionForm(StripEmojisMixin, RedactorAttachtorFormMixIn, EditIdeaBaseForm):
    perm_class = CanEditInitiative
    strip_emoji_fields = ['description']

    class Meta:
        model = Initiative
        fields = ('description', )


class EditIdeaOwnersForm(EditIdeaBaseForm):
    perm_class = CanEditInitiative

    # TODO: Ask confirmation if all owners are to be removed.
    owners = ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        label=_("Idean omistajat"),
        help_text=_("Syötä idean omistajien Nuortenideat.fi käyttäjätunnukset"),
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.idea = kwargs["instance"]
        kwargs.setdefault("initial", {})
        kwargs["initial"]["owners"] = self.idea.owners.all()
        super(EditIdeaOwnersForm, self).__init__(*args, **kwargs)

    def send_email_notification(self):
        receivers = set(self.initial["owners"]) | set(self.cleaned_data["owners"])
        for receiver in receivers:
            send_email(
                _("Idean omistajia muutettu."),
                "content/email/owner_change.txt",
                {"idea": self.idea},
                [receiver.settings.email],
                receiver.settings.language
            )

    def save(self, commit=True):
        changed = self.has_changed and "owners" in self.changed_data
        obj = super(EditIdeaOwnersForm, self).save(commit=commit)
        if changed and self.cleaned_data["owners"]:
            self.send_email_notification()
        return obj

    class Meta:
        model = Idea
        fields = ('owners', )


class EditInitiativeTagsForm(EditIdeaBaseForm):
    perm_class = CanEditInitiative

    tags = ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        label=_("Aiheet"), required=False
    )

    class Meta:
        model = Initiative
        fields = ('tags', )


class EditIdeaOrganizationsForm(EditIdeaBaseForm):
    perm_class = CanEditInitiative

    target_organizations = forms.MultipleChoiceField(
        choices=[],
        widget=Select2Multiple,
        label=_("Organisaatiot")
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(EditIdeaOrganizationsForm, self).__init__(*args, **kwargs)
        self.fields['target_organizations'].choices = get_organization_choices(user, True)

    class Meta:
        model = Idea
        fields = ('target_organizations', )


def validate_transfer_date(value):
    max_date = datetime.now().date() + relativedelta(
        days=MAX_DAYS_TO_IDEA_AUTO_TRANSFER)

    if not value:
        return value

    if value < datetime.now().date():
        raise forms.ValidationError(_("Mennyttä päivämäärää ei voi valita"))
    elif value > max_date:
        raise forms.ValidationError(
            _("Et voi valita suurempaa päivämäärää kuin %(value)s"),
            params={'value': date_filter(max_date, 'SHORT_DATE_FORMAT')},)

    return value


def get_transfer_date_start_date():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def get_transfer_date_end_date():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + \
           relativedelta(days=MAX_DAYS_TO_IDEA_AUTO_TRANSFER)


class EditIdeaSettingsForm(ModelForm):
    perm_class = CanChangeIdeaSettings

    def __init__(self, *args, **kwargs):
        super(EditIdeaSettingsForm, self).__init__(*args, **kwargs)

        if self.instance.auto_transfer_at:
            self.fields['auto_transfer_at'].validators.append(validate_transfer_date)
        else:
            self.fields.pop('auto_transfer_at')

    class Meta:
        model = Idea
        fields = ('premoderation', 'commenting_closed', 'interaction', 'auto_transfer_at')
        widgets = {
            'interaction': RadioSelect,
            'auto_transfer_at': NukaDateTimePicker(
                options={
                    "format": "DD.MM.YYYY",
                    "viewMode": "days",
                    'startDate': get_transfer_date_start_date(),
                    'endDate': get_transfer_date_end_date(),
                    'pickTime': False,
                    'allowInputToggle': True,
                }
            ),
        }


class EditIdeaPictureForm(ModelForm):
    picture = forms.ImageField(label=_("Valitse kuva"), widget=forms.FileInput,
                               required=False)

    picture_alt_text = forms.CharField(label=_("Mitä kuvassa on? (kuvaus suositeltava)"),
                                       required=False)

    def __init__(self, *args, **kwargs):
        super(EditIdeaPictureForm, self).__init__(*args, **kwargs)
        if self.instance.picture:
            self.fields['picture'].label = _("Vaihda kuva")

    class Meta:
        model = Idea
        fields = ('picture', 'picture_alt_text')


class DummyPictureForm(ModelForm):
    perm_class = CanEditInitiative

    def save(self):
        pass

    class Meta:
        model = Idea
        fields = ()


class AdditionalDetailForm(RedactorAttachtorFormMixIn, ModelForm):

    # Redactor-field needs a unique id to work, when using multiple forms on same page
    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs and kwargs['instance'].pk is not None:
            kwargs['prefix'] = 'pre-{}'.format(kwargs['instance'].pk)
        super(AdditionalDetailForm, self).__init__(*args, **kwargs)

    def clean_detail(self):
        return strip_emojis(self.cleaned_data['detail'])

    class Meta:
        model = AdditionalDetail
        fields = ('detail',)


class CreateQuestionBaseForm(forms.ModelForm):

    tags = ModelMultipleChoiceField(label=_("Aiheet"), widget=Select2Multiple,
                                    queryset=Tag.objects.all(), required=False)


class CreateQuestionForm(RedactorAttachtorFormMixIn, CreateQuestionBaseForm):
    title = forms.CharField(max_length=255, label=_("Otsikko"))
    description = RedactorAttachtorField(label=_("Viesti"))

    class Meta:
        model = Question
        fields = ('title', 'description', 'tags')
        required = ('description', )


class CreateQuestionFormAnon(CreateQuestionBaseForm):

    user_name = forms.CharField(label=_('Lähettäjän nimi'))
    user_email = forms.CharField(label=_('Sähköpostiosoite'), required=False,
                                 help_text=_("Kirjoita sähköpostiosoitteesi, jos haluat "
                                             "ilmoituksen kun kysymystä kommentoidaan "
                                             "tai siihen tulee vastaus organisaatiolta."))
    captcha = NoReCaptchaField(
        label=_('Tarkistuskoodi'),
        error_messages={'invalid': _('Virheellinen tarkistuskoodi.')}
    )
    description = forms.CharField(label=_('Viesti'), widget=forms.Textarea)

    class Meta:
        model = Question
        fields = ('title', 'description', 'tags', 'user_name', 'user_email')


class InitiativeSearchForm(forms.ModelForm):
    organizations = ModelMultipleChoiceField(
        queryset=Organization.objects.active(),
        label=_("Rajaa organisaatiolla"),
        required=False
    )

    tags = ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        label=_("Rajaa aiheella"),
        required=False
    )

    municipalities = ModelMultipleChoiceField(
        queryset=Municipality.objects.natural().active(),
        label=_("Rajaa paikkakunnalla"),
        required=False
    )

    def filtrate(self, idea_qs):
        organizations = self.cleaned_data.get('organizations', None)
        tags = self.cleaned_data.get('tags', None)
        municipalities = self.cleaned_data.get("municipalities", None)

        if organizations:
            idea_qs = idea_qs.filter(
                Q(target_organizations__in=organizations) |
                Q(initiator_organization__in=organizations)
            )
        if tags:
            idea_qs = idea_qs.filter(
                tags__in=tags
            )
        if municipalities:
            idea_qs = idea_qs.filter(
                target_organizations__municipalities__in=municipalities
            )

        return idea_qs

    def save(self, commit=True):
        raise Exception("Ei sallittu")


class IdeaStatusForm(forms.ModelForm):
    FIELD_STATUS = 'status'
    FIELD_VISIBILITY = 'visibility'

    SEARCH_STATUS_CHOICES = (
        (Idea.STATUS_PUBLISHED,      _("Avoin")),
        (Idea.STATUS_TRANSFERRED,    _("Viety eteenpäin")),
        (Idea.STATUS_DECISION_GIVEN, _("Vastaus annettu")),
        (Idea.VISIBILITY_ARCHIVED,   _("Arkistoitu"))
    )

    STATUS_FIELD_MAP = {
        Idea.STATUS_PUBLISHED: FIELD_STATUS,
        Idea.STATUS_TRANSFERRED: FIELD_STATUS,
        Idea.STATUS_DECISION_GIVEN: FIELD_STATUS,
        Idea.VISIBILITY_ARCHIVED: FIELD_VISIBILITY,
    }

    status = forms.ChoiceField(choices=(('', _("Kaikki")), ) + SEARCH_STATUS_CHOICES,
                               widget=AutoSubmitButtonSelect, required=False, label=False)

    def filter_status(self, qs, publicity_filter=True):
        status = self.cleaned_data.get('status', None)
        if status:
            status_field = self.STATUS_FIELD_MAP[int(status)]
            qs = qs.filter(**{status_field: status})
            if status_field == self.FIELD_VISIBILITY \
                    and int(status) == Idea.VISIBILITY_ARCHIVED:
                qs = self.filter_visibility_archived_qs(qs)

        if publicity_filter:
            if not status or not self.FIELD_VISIBILITY == status_field:
                qs = qs.filter(visibility=Initiative.VISIBILITY_PUBLIC)

        return qs

    def filter_visibility_archived_qs(self, qs):
        if not self.is_authenticated:
            return qs.none()

        # if not moderator, then only show archived ideas owned by user
        if not self.user.is_moderator:
            options = {'owners': self.user}

            # for organization admins even targeted ideas
            if self.user.organization_ids:
                qs = qs.filter(
                    Q(**options) |
                    Q(initiator_organization__in=self.user.organization_ids) |
                    Q(target_organizations__in=self.user.organization_ids))
            else:
                qs = qs.filter(**options)
        return qs

    class Meta:
        pass


class IdeaSearchForm(WordSearchMixin, InitiativeSearchForm, IdeaStatusForm):
    pk_order_field = 'content_initiative.id'
    default_order_by = '-published'

    words = forms.CharField(label=_("Hae ideaa"), required=False)

    organization_initiated = forms.BooleanField(
        label=_('Vain organisaatioiden luomat ideat'),
        required=False
    )

    user = None
    is_authenticated = False

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.is_authenticated = self.user.is_authenticated() if \
            hasattr(self.user, 'is_authenticated') else False

        super(IdeaSearchForm, self).__init__(*args, **kwargs)

        # Set the result count to the status labels.
        new_choices = []
        for status, label in self.fields['status'].choices:
            if status:
                status_field = self.STATUS_FIELD_MAP[int(status)]
                queryset = Idea._default_manager.filter(**{status_field: status})

                if status_field != self.FIELD_VISIBILITY:
                    queryset = queryset.filter(visibility=Initiative.VISIBILITY_PUBLIC)
                else:
                    if status == Idea.VISIBILITY_ARCHIVED:
                        # remove option "archived" if not authenticated
                        if not self.is_authenticated:
                            continue
                        queryset = self.filter_visibility_archived_qs(queryset)
            else:
                queryset = Idea.objects.exclude(visibility=Idea.VISIBILITY_ARCHIVED)

            label = "{} ({})".format(label, queryset.count())
            new_choices.append((status, label))

        self.fields['status'].choices = new_choices

    def get_haystack(self, obj):
        return [obj.search_text.strip(), str(obj.title)]

    def filtrate(self, qs):
        publicity_filter = True
        if self.is_authenticated and self.user.is_moderator:
            publicity_filter = False

        words = self.cleaned_data.get('words', None)
        organization_initiated = self.cleaned_data.get("organization_initiated", None)

        qs = super(IdeaSearchForm, self).filtrate(qs)
        qs = self.filter_status(qs, publicity_filter)

        if organization_initiated:
            qs = qs.exclude(initiator_organization__isnull=True)

        if words:
            return self.word_search(words.strip(), qs)

        return qs.order_by(self.default_order_by)

    class Meta:
        model = Idea
        fields = ('organizations', 'tags')


class AttachmentUploadForm(FileUploadForm):
    file = SaferFileField()

    def __init__(self, *args, **kwargs):
        self.uploader = kwargs.pop('uploader')
        self.upload_group = kwargs.pop('upload_group')
        super(FileUploadForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned = super(AttachmentUploadForm, self).clean()
        limits = settings.ATTACHMENTS
        if 'file' in cleaned:
            file = cleaned['file']
            if file.size > limits['max_size']:
                raise forms.ValidationError(ugettext("Tiedosto ylittää kokorajoituksen."))
            if self.upload_group is not None:
                obj_totals = self.upload_group.upload_set.aggregate(
                    count=Count('id'), total_size=Sum('size')
                )
                if (obj_totals['count'] or 0) >= limits['max_attachments_per_object']:
                    raise forms.ValidationError(
                        ugettext("Liian monta liitetiedostoa lisätty.")
                    )
            uploader_total = Upload.objects.filter(
                uploader=self.uploader,
                created__gte=timezone.now()-limits['max_size_per_uploader_timeframe']
            ).aggregate(size=Sum('size'))
            if (uploader_total['size'] or 0) + file.size > \
                    limits['max_size_per_uploader']:
                raise forms.ValidationError(
                    ugettext("Olet lisännyt liian monta liitetiedostoa. "
                             "Yritä myöhemmin uudestaan.")
                )
        return cleaned


class KuaTransferBlankForm(forms.ModelForm):
    def save(self, commit=True):
        raise Exception("i don't want to be saved")

    class Meta:
        model = Idea
        fields = ()


class KuaTransferMembershipReasonForm(KuaTransferBlankForm):
    MEMBERSHIP_COMMUNITY = 'community'
    MEMBERSHIP_COMPANY = 'company'
    MEMBERSHIP_PROPERTY = 'property'
    MEMBERSHIP_NONE = 'none'

    MEMBERSHIP_CHOICES = (
        (MEMBERSHIP_COMMUNITY,  _("Nimenkirjoitusoikeus yhteisössä, laitoksessa tai "
                                  "säätiössä, jonka kotipaikka on aloitetta koskevassa "
                                  "kunnassa")),
        (MEMBERSHIP_COMPANY,    _("Nimenkirjoitusoikeus yrityksessä, jonka kotipaikka on "
                                  "aloitetta koskevassa kunnassa")),
        (MEMBERSHIP_PROPERTY,   _("Hallinta-oikeus tai omistus kiinteään omaisuuteen "
                                  "aloitetta koskevassa kunnassa")),
        (MEMBERSHIP_NONE,       _("Ei mitään näistä")),
    )
    membership = forms.ChoiceField(choices=MEMBERSHIP_CHOICES, widget=RadioSelect,
                                   label=_("Onko sinulla jokin seuraavista?"))

    def clean_membership(self):
        value = self.cleaned_data['membership']
        if value == self.MEMBERSHIP_NONE:
            raise forms.ValidationError(ugettext("Et voi tehdä kuntalaisaloitetta "
                                                 "kuntaan, jossa et ole jäsenenä."))
        return value

    class Meta:
        model = Idea
        fields = ('membership', )


class PublishIdeaForm(forms.Form):
    DEFAULT_TRANSFER_DATE = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0) + relativedelta(days=14)

    transfer_date = forms.DateField(
        label=_("Valitse päivämäärä, jolloin idea lähtee automaattisesti eteenpäin "
                "käsittelyyn asiasta vastaavalle henkilölle"),
        help_text=_("Voit muuttaa päivämäärän, jolloin idea lähetetään käsittelyyn "
                    "(oletuksena kahden viikon päästä). Mitä enemmän kannatusta ja "
                    "kommentteja idea saa, sitä todennäköisemmin se pääsee toteutukseen "
                    "ja käsittelyyn päätöksenteossa. Jaa siksi ideasi kavereille "
                    "kannatettavaksi ja kommentoitavaksi!"),
        widget=NukaDateTimePicker(options={
            "format": "DD.MM.YYYY",
            "viewMode": "days",
            'defaultDate': DEFAULT_TRANSFER_DATE,
            'startDate': get_transfer_date_start_date(),
            'endDate': get_transfer_date_end_date(),
            'pickTime': False,
            'allowInputToggle': True,
        }),
        required=True,
        validators=[validate_transfer_date],
    )

    included_surveys = ModelMultipleChoiceField(queryset=IdeaSurvey.objects.none(),
                                                label='', required=False)

    agreement = forms.BooleanField(
        label=_("Ymmärrän, että idean julkaisun jälkeen, nimeni ja sähköpostiosoitteeni "
                "välitetään idean vastaanottajalle. Idean vastanottaja on henkilö, joka "
                "kirjoittaa vastauksen tai päätöksen asiaan tai toimittaa sen eteenpäin "
                "jatkokäsittelyyn oikealle henkilölle."),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        idea = kwargs.pop('instance')
        super(PublishIdeaForm, self).__init__(*args, **kwargs)
        self.fields['included_surveys'].queryset = idea.idea_surveys.drafts()

    class Meta:
        fields = ()


class EditIdeaSurveyNameForm(HiddenLabelMixIn, ModelForm):

    class Meta:
        model = IdeaSurvey
        fields = ('title', )
