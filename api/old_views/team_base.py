from rest_framework import permissions, viewsets, status, mixins, serializers, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.shortcuts import get_object_or_404
from rest_framework.settings import api_settings
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
import functools

from ..models import Team
from ..permissions import IsAdminMemberOrReadOnly, IsOwnerOrReadOnly, IsMemberUser

kTeamId = 'team_id'


def team_queried_view(func):
    """ Modifies the default signature of the list get view by popping the pk from the
        query params and adding it as an argument of the function, doing validation as necessary
    """

    @functools.wraps(func)
    def wrapper(self, request: Request):
        if not (pk := request.query_params.pop(kTeamId, None)):
            return Response({"msg": "missing required parameter team"}, status=status.HTTP_400_BAD_REQUEST)

        return func(self, request, pk)

    return wrapper


# This base class provides the basic interface that most user accessible models in our
# system should fit
class TeamRelatedViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdminMemberOrReadOnly,
        IsMemberUser,
    ]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    schema_dict = dict(
        parameters=[
            OpenApiParameter(name=kTeamId, description='id which references a team object', required=True, type=int)
        ],
    )

    @staticmethod
    def get_success_headers(data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    # this will create a record of the inherited class
    @action(
        methods=["POST"], detail=False, permission_classes=[permissions.IsAuthenticated, IsMemberUser]
    )
    def create_record(self, request, *args, **kwargs):
        """
        Inserts a record into the db, expects the json as seen below\n
        """
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            team = serializer.validated_data["team_id"]

            # make sure we're actually allowed to access this team
            self.check_object_permissions(request, team)
            record = serializer.save()

            serialized = self.serializer_class(record)
            return Response(serialized.data, status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            return Response({"msg": e.detail}, e.status_code)

    # this will list all entries of a given type (through inheritance)
    # whose team relation correlates with the primary key

    @extend_schema(parameters=[
        OpenApiParameter(name=kTeamId, description='id which references a team object', required=True, type=int),
        OpenApiParameter(name="ordering", description='specify field in which to order by', required=False, type=str),
        OpenApiParameter(name="page",
                         description='specify which page of information to access',
                         required=False, type=int),
    ])
    @action(detail=False, methods=["GET"], permission_classes=permission_classes)
    @team_queried_view
    def list_team(self, request, pk=None):
        """
        Lists all the records which belong to the team associated with {id}.
        Options: ordering, search, page
        """

        queryset = self.filter_queryset(self.get_queryset().filter(
            team__id=pk
        ).filter(
            deactivated=None
        ))
        serializer = self.serializer_class(queryset, many=True)

        team = get_object_or_404(Team, pk=pk)
        self.check_object_permissions(request, team)
        return Response(serializer.data, status.HTTP_200_OK)
