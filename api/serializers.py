from rest_framework import serializers
from django.contrib.auth import get_user_model
from . import models as api_models
from django.shortcuts import get_object_or_404
import sys

User = get_user_model()


class PrimaryKeySerializedField(serializers.PrimaryKeyRelatedField):
    """
    Custom field subclassing PrimaryKeyRelated
    On writes, this allows us to specify the primary key for a resource
    On reads, this will serialize the associated resource, nesting it
    within the outer json
    """

    def __init__(self, **kwargs):
        serializer = kwargs.pop('serializer')

        if isinstance(serializer, str) and (s_class := getattr(sys.modules[__name__], serializer, None)):
            self.serializer = s_class
        elif issubclass(serializer, serializers.BaseSerializer):
            self.serializer = serializer
        else:
            raise Exception("invalid serializer specified!")

        self.many = kwargs.get('many')
        super().__init__(**kwargs)

    def to_representation(self, value):
        if self.pk_field is not None:
            return self.pk_field.to_representation(value.pk)

        if self.many:
            return self.serializer(value, many=self.many).data

        else:
            instance = self.queryset.get(pk=value.pk)
            return self.serializer(instance).data


class UserSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()

    class Meta:
        model = get_user_model()
        fields = ["id", "email", "first_name", "last_name", "username"]


class TeamSerializer(serializers.ModelSerializer):
    # make the following fields read only
    id = serializers.ReadOnlyField()
    ticket_head = serializers.ReadOnlyField()
    object_uuid = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.Team
        fields = [
            "id",
            "name",
            "object_uuid",
            "ticket_head",
            "created",
            "activated",
            "deactivated",
        ]


class TagSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.Tag
        fields = [
            "id", "team_id", "object_uuid", "title", "created", "activated",
            "deactivated"
        ]


class MemberSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    owner = UserSerializer(many=False, read_only=True)
    object_uuid = serializers.ReadOnlyField()
    team_id = serializers.ReadOnlyField(source="team.id")
    role = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.Member
        fields = [
            "id",
            "owner",
            "team_id",
            "object_uuid",
            "role",
            "bio",
            "pronouns",
            "created",
            "activated",
            "deactivated",
        ]


class TicketCommentSerializer(serializers.ModelSerializer):
    ticket_id = serializers.ReadOnlyField(source="ticket.id")
    team_id = serializers.ReadOnlyField(source="team.id")
    owner = UserSerializer(many=False, read_only=True)

    class Meta:
        model = api_models.TicketComment

        fields = [
            "id",
            "ticket_id",
            "team_id",
            "owner",
            "object_uuid",
            "content",
            "created",
            "activated",
            "deactivated",
        ]


class TicketStatusSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    object_uuid = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.TicketStatus
        fields = [
            "id", "object_uuid", "title", "created", "activated", "deactivated"
        ]


class TicketTagSerializer(serializers.ModelSerializer):
    tag = TagSerializer(many=False, read_only=True)
    object_uuid = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.TicketTag
        fields = ["tag", "created", "object_uuid", "activated", "deactivated"]


class TicketNodeSerializer(serializers.ModelSerializer):
    ticket_id = serializers.ReadOnlyField()

    class Meta:
        model = api_models.TicketNode
        fields = ["ticket_id"]


class TicketSerializer(serializers.ModelSerializer):
    """
    On writes,\n
    - tag_list expects a list of primary keys\n
    - status expects a primary key\n
    On reads,\n
    - tag_list is a list of serialized tag objects\n
    - status is a serialized status object\n

    The autogenerated documentation does not account for this
    """

    id = serializers.ReadOnlyField()

    tag_list = PrimaryKeySerializedField(many=True,
                                         required=False,
                                         queryset=api_models.Tag.objects.all(),
                                         serializer=TagSerializer)

    parent = serializers.IntegerField(write_only=True, required=False)
    object_uuid = serializers.ReadOnlyField()

    owner = UserSerializer(many=False, read_only=True)
    ticket_number = serializers.ReadOnlyField()
    comments = TicketCommentSerializer(many=True, required=False)

    assigned_user = PrimaryKeySerializedField(many=False,
                                              required=False,
                                              queryset=User.objects.all(),
                                              serializer=UserSerializer)

    status = PrimaryKeySerializedField(
        many=False,
        required=False,
        queryset=api_models.TicketStatus.objects.all(),
        serializer=TicketStatusSerializer)

    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.Ticket
        fields = [
            "id",
            "ticket_number",
            "tag_list",
            "parent",
            "owner",
            "object_uuid",
            "assigned_user",
            "status",
            "title",
            "description",
            "comments",
            "created",
            "activated",
            "deactivated",
        ]

    # this creates a record from the json, modifying the keys
    def create(self, validated_data):
        tag_list = validated_data.pop('tag_list', None)
        parent = validated_data.pop('parent', None)

        if parent:
            # warning: add_child may throw path_overflow
            parent_instance = get_object_or_404(api_models.Ticket, pk=parent)
            ticket = parent_instance.add_child(**validated_data)

        else:
            ticket = api_models.Ticket.add_root(**validated_data)

        api_models.TicketTag.create_all(tag_list, ticket)

        return ticket

    # update the instance with validated_data
    def update(self, instance, validated_data):
        tag_list = validated_data.pop('tag_list', None)
        parent = validated_data.pop('parent', None)

        # TODO: figure out update semantics for adding a subticket
        # if parent:
        #     parent_instance = get_object_or_404(api_models.Ticket, pk=parent)
        #     parent_instance.move(instance, pos='last-child')

        api_models.TicketTag.delete_difference(tag_list, instance)

        return super().update(instance, validated_data)


class EventSerializer(serializers.ModelSerializer):
    """
    On writes,\n
    - user expects a primary key\n

    On reads,\n
    - user is a serialized user object\n

    The autogenerated documentation does not account for this
    """

    id = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    event_type = serializers.ReadOnlyField()
    user = UserSerializer(many=False)
    object_id = serializers.ReadOnlyField()

    class Meta:
        model = api_models.Event
        fields = [
            "id", "team_id", "created", "event_type", "user", "user_id",
            "description", "object_id"
        ]
