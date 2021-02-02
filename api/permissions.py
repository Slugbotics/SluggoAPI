from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from hashlib import md5
from .models import Member, Team


class BaseMemberPermissions(BasePermission):
    # this will throw a member not found exception

    @staticmethod
    def retrieveMemberRecord(username, obj):
        team_id = obj.id if isinstance(obj, Team) else obj.team.id
        team_id = "{}".format(team_id)
        member_pk = (
            md5(team_id.encode()).hexdigest() + md5(username.encode()).hexdigest()
        )
        return Member.objects.get(pk=member_pk)


# only permit this if the user is approved
class IsMemberUser(BaseMemberPermissions):
    def has_object_permission(self, request, view, obj):

        try:
            member_record = self.retrieveMemberRecord(request.user.username, obj)
            permit = member_record.role != Member.Roles.UNAPPROVED
        except Member.DoesNotExist:
            permit = False

        return permit


class IsAdminMemberOrReadOnly(BaseMemberPermissions):
    """
    Custom permission to allow admin of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method not in SAFE_METHODS:
            try:
                # Write permissions are only allowed to the owner of the object, or admin.

                member_record = self.retrieveMemberRecord(
                    request.user.username, obj
                )
                permit = member_record.role == Member.Roles.ADMIN

            except Member.DoesNotExist:
                permit = False

        else:
            permit = True
        return permit


class IsOwnerOrReadOnly(BaseMemberPermissions):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.

        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user
