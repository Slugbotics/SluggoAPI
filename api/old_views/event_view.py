from ..models import (
    Event
)

from ..serializers import (
    EventSerializer
)

from .team_base import *


class EventViewSet(TeamRelatedViewSet, mixins.DestroyModelMixin):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdminMemberOrReadOnly,
        IsMemberUser,
    ]

    @extend_schema(**TeamRelatedViewSet.schema_dict)
    @action(detail=True, methods=["GET"], permission_classes=[
        permissions.IsAuthenticated, IsMemberUser
    ])
    @team_queried_view
    def list_team(self, request, pk=None):
        return super().list_team(request, pk)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.check_object_permissions(request, instance)
            self.perform_destroy(instance)
            return Response({"msg": "okay"}, status=status.HTTP_204_NO_CONTENT)
        except Event.DoesNotExist:
            return Response({"msg": "no such event"}, status=status.HTTP_404_NOT_FOUND)
