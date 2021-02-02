from django.utils import timezone
from rest_framework import exceptions

from django.contrib.auth import get_user_model

from ..models import (
    Member,
    Team,
)
from ..serializers import MemberSerializer, TeamSerializer, UserSerializer

from .team_base import *


class MemberViewSet(
    TeamRelatedViewSet
):
    """
    Reads handled by the mixins, and use permission_classes
    """

    queryset = Member.objects.all()

    permission_classes = [
        permissions.IsAuthenticated,
        IsMemberUser,
        IsOwnerOrReadOnly
    ]

    serializer_class = MemberSerializer

    @staticmethod
    def get_success_headers(data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    # require only that the user is authenticated to create their profile / join a team
    # manually defining this since we want to offer this endpoint for any authenticated user
    @action(
        methods=["POST"], detail=False, permission_classes=[permissions.IsAuthenticated]
    )
    def create_record(self, request, *args, **kwargs):
        team_id = request.data.get("team_id")

        try:
            team = get_object_or_404(Team, id=team_id)
            serializer = MemberSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            serializer.save(owner=request.user, team=team)

            headers = self.get_success_headers(serializer.data)
        except Team.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    # this facilitates editing the user profile associated with a team
    # this function is keyed in by the join_id which is the team_id
    # concatenated with the md5 of the user_id
    #
    # affects both the member record and the associated user record
    def update(self, request, *args, **kwargs):
        """
        Update the member record for a particular user, the one associated with the pk.
        A user is limited by the fields they have access to. While the entire member record
        is expected, calls through update only modify the bio field and the first / last name
        field of the associated user object.
        """
        kwargs["partial"] = True
        pk = kwargs.pop("pk")

        # serialize the input, then update only a select number of fields
        try:
            member_serializer = MemberSerializer(data=request.data)
            member_serializer.is_valid(raise_exception=True)

            user_serializer = UserSerializer(data=request.data.get("user"))
            user_serializer.is_valid(raise_exception=True)

            Member.objects.filter(pk=pk).update(**member_serializer.validated_data)

        except exceptions.ValidationError as e:
            return Response({"msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return super().update(request, partial=True)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[permissions.IsAuthenticated, IsAdminMemberOrReadOnly],
    )
    def approve(self, request, pk=None):
        """
        Approve the member record associated with the pk.
        This can only be done by authenticated admins.
        """
        # approve the user.
        self.check_object_permissions(request, self.get_object())

        try:
            member = get_object_or_404(Member, pk=pk)
            member.activated = timezone.now()

            if member.role == Member.Roles.UNAPPROVED:
                member.role = Member.Roles.APPROVED
                member.save(update_fields=["activated", "role"])

            return Response({"msg": "okay"}, status=status.HTTP_200_OK)

        except Member.DoesNotExist:
            return Response({"msg": "failure"}, status.HTTP_404_NOT_FOUND)

    # make the user an admin if not done already
    # this call is essentially idempotent and only modifies the user record when user was not previously activated
    # the user does not need to be approved for them to become an admin
    @action(detail=True, methods=["patch"], permission_classes=[permissions.IsAuthenticated, IsAdminMemberOrReadOnly])
    def make_admin(self, request, pk=None):
        """
        Make the user, whose member record is associated with a primary key, an admin.
        This can only be done by an authenticated admin.
        """
        self.check_object_permissions(request, self.get_object())

        try:
            member = get_object_or_404(Member, pk=pk)
            member.activated = timezone.now()

            if member.role != Member.Roles.ADMIN:
                member.role = Member.Roles.ADMIN
                member.save(update_fields=["role"])

            return Response({"msg": "okay"}, status=status.HTTP_200_OK)

        except Member.DoesNotExist:
            return Response({"msg": "failure"}, status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["patch"], permission_classes=permission_classes)
    def leave(self, request, pk=None):
        """ With the primary key, deactivate the associated record """
        self.check_object_permissions(request, self.get_object())

        try:
            member = get_object_or_404(Member, pk=pk)
            member.deactivated = timezone.now()
            member.save()

            return Response({"msg": "okay"}, status=status.HTTP_200_OK)

        except Member.DoesNotExist:
            return Response({"msg": "failure"}, status=status.HTTP_404_NOT_FOUND)


class TeamViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = Team.objects.all()

    permission_classes = [permissions.IsAuthenticated, IsAdminMemberOrReadOnly]

    serializer_class = TeamSerializer

    @staticmethod
    def get_success_headers(data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    @action(methods=["POST"], detail=False, permission_classes=[permissions.IsAuthenticated])
    def create_record(self, request, *args, **kwargs):
        """
        Create a team record. The user which calls this endpoint is given the admin role for this organization.
        """

        # serialize the request data.
        team_serializer = TeamSerializer(data=request.data)
        team_serializer.is_valid(raise_exception=True)
        team = team_serializer.save()  # if we've made it this far, save the record

        # construct a member record from the user information
        member = Member.objects.create(
            owner=request.user,
            team=team,
            role="AD",
            activated=timezone.now()
        )
        member.save()

        headers = self.get_success_headers(team_serializer.data)

        return Response(team_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
