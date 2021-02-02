from django.utils import timezone
from treebeard import exceptions as t_except
from django.core.exceptions import SuspiciousOperation
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.request import Request

from ..models import (
    Ticket,
    TicketComment,
    TicketStatus,
    Tag,
    TicketTag,
    TicketNode
)

from ..serializers import (
    TicketSerializer,
    TicketCommentSerializer,
    TicketStatusSerializer,
    TagSerializer,
    TicketNodeSerializer
)

from .team_base import *

User = get_user_model()


class TicketViewSet(
    TeamRelatedViewSet
):
    """
    Actions that provide CRUD coverage for tickets
    """
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    search_fields = ['^team__name', '^team__description', '^title', '^description', '^status__title',
                     '^assigned_user__first_name']
    permission_classes = [
        permissions.IsAuthenticated,
        IsOwnerOrReadOnly | IsAdminMemberOrReadOnly,
        IsMemberUser,
    ]
    ordering_fields = ['created', 'activated']
    filterset_fields = ['owner__username']

    # require that the user is a member of the team to create a ticket
    # manually defining this since we want to offer this endpoint for any authenticated user
    @action(
        methods=["POST"], detail=False, permission_classes=[permissions.IsAuthenticated, IsMemberUser]
    )
    def create_record(self, request, *args, **kwargs):
        """
        Creates a record from the json included in the data field\n
        See below for details on what the json\n
        """
        try:
            serializer = TicketSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            team = serializer.validated_data["team_id"]
            tag_list = serializer.validated_data.pop("tag_id_list", None)
            parent_id = serializer.validated_data.pop("parent_id", None)

            # once we have a team record, make sure we are allowed to access it
            self.check_object_permissions(request, team)
            ticket = serializer.save(
                owner=self.request.user
            )

            # the above serializer has already confirmed that each tag_id is valid
            if tag_list:
                for tag in tag_list:
                    ticket_tag = TicketTag.objects.create(
                        team=team, tag=tag, ticket=ticket
                    )
                    ticket_tag.save()

            # query for the parent. If the id was included, query for the
            # associated root node. if not, insert the ticket as a root
            if parent_id:
                parent_ticket = get_object_or_404(Ticket, pk=parent_id)
                parent_node = get_object_or_404(TicketNode, ticket=parent_ticket)
                parent_node.add_child(ticket=ticket)
            else:
                TicketNode.add_root(ticket=ticket)

            serialized = TicketSerializer(ticket)

            return Response(serialized.data, status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            return Response({"msg": e.detail}, e.status_code)

    # overloading this function in order to attach a list of children
    def retrieve(self, request, *args, **kwargs):
        """
        Queries the database using the {id} selecting the primary key field
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        response = serializer.data
        root = TicketNode.objects.get(ticket=instance)
        if root:
            response["children"] = [TicketNodeSerializer(child_instance).data for child_instance in root.get_children()]

        return Response(response)

    @action(
        detail=True,
        methods=['patch'],
        permission_classes=[permissions.IsAuthenticated, IsMemberUser]
    )
    def update_status(self, request, pk=None):
        """
        update the ticket's status\b
        if a ticket status is present in the data, update the ticket's status\n
        this assumes that the status is already created\n
        """
        self.check_object_permissions(request, self.get_object())

        status_id = request.data('status_id')
        if status_id:
            ticket = get_object_or_404(Ticket, pk=pk)
            ticket.status = get_object_or_404(TicketStatus, pk=status_id)
            ticket.save(update_fields=['status'])

        return Response({"msg": "okay"}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["delete"],
        permission_classes=permission_classes,
    )
    def delete(self, request, pk=None):
        """
        Deactivates, but do not delete the ticket associated with {id}\n
        """
        try:
            instance = get_object_or_404(Ticket, pk=pk)
            self.check_object_permissions(request, instance)
            instance.deactivated = timezone.now()
            instance.save()
            return Response({"msg": "okay"}, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            return Response({"msg": "no such ticket"}, status=status.HTTP_404_NOT_FOUND)

    # TODO: probably move this to a model
    def _add_subticket(self, parent, child):
        try:
            # fetch the associated node
            parent_node = get_object_or_404(TicketNode, ticket=parent)
            ticket_node_filter = TicketNode.objects.filter(ticket=child)

            if ticket_node_filter:
                # if it exists and is root, move as child
                if len(ticket_node_filter) != 1:
                    raise SuspiciousOperation("Invalid request; the tree got messed up")

                ticket_node = ticket_node_filter[0]
                if ticket_node.is_root():
                    ticket_node.move(target=parent_node, pos="last-child")
                else:
                    return Response({"msg": "ticket already part of a graph"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                parent_node.add_child(ticket=child)

            return Response({"msg": "okay"}, status=status.HTTP_200_OK)
        except (
                t_except.InvalidMoveToDescendant, t_except.InvalidPosition,
                t_except.NodeAlreadySaved, t_except.PathOverflow
        ):
            return Response({"msg": "invalid tree operation"}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['patch'],
        permission_classes=permission_classes
    )
    def add_as_subticket(self, request, pk=None):
        """
        add a ticket as a subticket of the ticket associated with pk
        """
        try:
            # validate
            ticket = self.get_object()
            parent = get_object_or_404(Ticket, pk=request.data.get("parent_id"))
            self.check_object_permissions(request, ticket)
            self.check_object_permissions(request, parent)

            # serialize the parent ticket

            return self._add_subticket(parent, ticket)

        except serializers.ValidationError as e:
            return Response({"msg": e.detail}, e.status_code)

    @action(
        detail=True,
        methods=['patch'],
        permission_classes=permission_classes
    )
    def add_subticket(self, request, pk=None):
        """
        add a subticket to the ticket associated with pk
        """
        try:
            # validate
            parent = self.get_object()
            child = get_object_or_404(Ticket, pk=request.data.get("child_id", None))
            self.check_object_permissions(request, parent)
            self.check_object_permissions(request, child)

            return self._add_subticket(parent, child)

        except serializers.ValidationError as e:
            return Response({'msg': e.detail}, e.status_code)

    @extend_schema(**TeamRelatedViewSet.schema_dict)
    @action(
        detail=False,
        methods=['GET'],
        permission_classes=permission_classes,
    )
    @team_queried_view
    def retrieve_user_tickets(self, request, pk=None):
        """
        {id} refers to a team
        retrieve all tickets which are owned / assigned to requesting user
        """
        team = get_object_or_404(Team, pk=pk)
        try:
            tickets = Ticket.retrieve_by_user(request.user, team)

            for ticket in tickets:
                self.check_object_permissions(request, ticket)

            serializer = self.serializer_class(tickets, many=True)

            return Response(serializer.data, status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response({"msg": "no such tickets"}, status.HTTP_404_NOT_FOUND)


class TicketCommentViewSet(viewsets.ModelViewSet):
    """
    all of these endpoints are deprecated for the time being
    """

    permission_classes = [
        permissions.IsAuthenticated,
        IsOwnerOrReadOnly | IsAdminMemberOrReadOnly,
    ]

    queryset = TicketComment.objects.all()
    serializer_class = TicketCommentSerializer

    @action(detail=False)
    def recent_comments(self, request, team_id=None):
        """ This call returns the first page of comments associated with the given team_id """
        pass


"""
all old_views inherit from TeamRelatedViewSet following
"""


class TicketStatusViewSet(
    TeamRelatedViewSet,
    mixins.DestroyModelMixin
):
    queryset = TicketStatus.objects.all()
    serializer_class = TicketStatusSerializer
    filterset_fields = ['title']


class TagViewSet(
    TeamRelatedViewSet,
    mixins.DestroyModelMixin
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
