from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404

from ..models import *
from ..docs import *
from ..permissions import *

"""
subclassing all the entire model viewset path in order to generate
documentation properly, and with minimal duplication
"""


class NewTeamRelatedBase(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsMemberUser]

    search_fields = ['^name', '^description']
    ordering_fields = ['created', 'activated']

    def check_permissions(self, request):
        super().check_permissions(request)
        super().check_object_permissions(request, self.get_team())

    def get_team(self):
        team_id = self.kwargs.get(TEAM_PK)
        return get_object_or_404(Team, pk=team_id)

    def get_queryset(self, *args, **kwargs):
        team_instance = self.get_team()
        return self.queryset.filter(team=team_instance)


class TeamRelatedRetrieveMixin(NewTeamRelatedBase, mixins.RetrieveModelMixin):
    @extend_schema(**TEAM_DETAIL_SCHEMA)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class TeamRelatedListMixin(NewTeamRelatedBase, mixins.ListModelMixin):
    @extend_schema(**TEAM_LIST_SCHEME)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TeamRelatedCreateMixin(NewTeamRelatedBase, mixins.CreateModelMixin):

    @extend_schema(**TEAM_DETAIL_SCHEMA)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # save the instance
        team_instance = self.get_team()
        serializer.save(team=team_instance)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TeamRelatedUpdateMixin(NewTeamRelatedBase, mixins.UpdateModelMixin):
    @extend_schema(**TEAM_DETAIL_SCHEMA)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class TeamRelatedDestroyMixin(NewTeamRelatedBase, mixins.DestroyModelMixin):
    @extend_schema(**TEAM_DETAIL_SCHEMA)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class TeamRelatedModelViewSet(TeamRelatedListMixin,
                              TeamRelatedCreateMixin,
                              TeamRelatedUpdateMixin,
                              TeamRelatedRetrieveMixin,
                              TeamRelatedDestroyMixin):
    """
    Similar to the implementation of the ModelViewSet, this collects
    the list, create, update, destroy, retrieve mixins but updates the schema
    to account for the hierarchical nature of the
    """
    pass








