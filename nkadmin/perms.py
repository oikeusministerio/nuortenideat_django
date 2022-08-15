# coding=utf-8

from __future__ import unicode_literals

from libs.permitter import perms
from nuka import perms as nuka
from account import perms as account


class ModeratorRightsUpdatable(nuka.BasePermission):
    def is_authorized(self):
        return self.user.moderator_rights_updatable()


CanAccessAdminPanel = perms.And(
    nuka.IsAuthenticated,
    perms.Or(nuka.IsModerator, nuka.IsAdmin),
)

CanEditUser = perms.And(
    nuka.IsAuthenticated,
    perms.Or(
        perms.And(
            account.OwnAccount,
            nuka.IsModerator
        ),
        perms.And(
            nuka.IsModerator,
            nuka.ObjectIsParticipant
        ),
        nuka.IsAdmin
    )
)

CanUpdateModeratorRights = perms.And(
    ModeratorRightsUpdatable,
    nuka.IsModerator
)
