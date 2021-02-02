"""
A REST API needs to provide a way of serializing and deserializing the models created into representations such as json.
We can do this by declaring serializers that work very similar to Django's forms. Create a file in the app directory
named serializers.py and create your classes.
"""
from rest_framework import serializers

from django.contrib.auth import get_user_model
from rest_framework.utils import model_meta

from django.conf import settings
from . import models as api_models
from django.db.models import Q
from django.shortcuts import get_object_or_404

User = get_user_model()


class PrimaryKeySerializedField(serializers.PrimaryKeyRelatedField):
    """ Custom field subclassing PrimaryKeyRelated
        On writes, this allows us to specify the primary key for a resource
        On reads, this will serialize the associated resource, nesting it
        within the outer json
    """

    def __init__(self, **kwargs):
        self.serializer = kwargs.pop('serializer')
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
    """
    Serializer Class for User model\n

    The fields that are serialized on reads:\n
        1. id: pk for this user\n
        2. email: email for this user\n

    The fields that are serialized on writes:\n
        1. first_name: first name for this user\n
        2. last_name: last name for this user\n

    """
    id = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()

    class Meta:
        model = get_user_model()
        fields = ["id", "email", "first_name", "last_name"]


class TeamSerializer(serializers.ModelSerializer):
    """
    Serializer Class for Team model\n

    The fields that are serialized on reads:\n
        1. id: pk for this model\n
        2. ticket_head: current count of tickets\n
        3. object_uuid: unique identifier for this team\n
        4. name: name of the team\n
        5. description: description for the team\n
        6. created: creation datetime\n
        7. activated: activation datetime\n
        8. deactivated: deactivation datetime\n

    The fields that are serialized on writes:\n
        1. name: name of team\n
        2. description: description of the team\n

    """
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
            "description",
            "object_uuid",
            "ticket_head",
            "created",
            "activated",
            "deactivated",
        ]


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer Class for Tag model\n

    The fields that are serialized on reads:\n
        1. id: pk for this model\n
        3. object_uuid: unique identifier for this object\n
        4. title: the title for this tag\n
        5. created: datetime for creation\n
        6. activated: datetime for activation\n
        7. deactivated: datetime for deactivation\n

    The fields that are serialized on writes:\n
        1. title: the title for this tag\n

    """
    id = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.Tag
        fields = ["id", "team_id",
                  "object_uuid",
                  "title", "created", "activated", "deactivated"]


class MemberSerializer(serializers.ModelSerializer):
    """
    Serializer Class for TicketTag model\n

    The fields that are serialized on reads:\n
        1. id: pk for this record\n
        2. owner: serialized user model for the owner of this record\n
        3. object_uuid: unique identifier for this object\n
        4. team_id: pk for the team associated with this member\n
        5. bio: bio / description for this member\n
        6. pronouns: pronouns for this member\n
        7. role: string field for the role of this member\n
        8. created: when this record was created\n
        9. activated: when this record was activated\n
        10. deactivated: when this record was deactivated\n

    The fields that are serialized on creates:\n
        1. bio: bio / description for this member\n
        2. pronouns: pronouns for this member\n

    The fields that are serializeds on updates:\n
        1. bio: bio / description for this member\n
        2. pronouns: pronouns for this member\n
        3. owner:\n
            a. first_name: the first name for the user model\n
            b. last_name: the last name for the user model\n

    """
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
    """
    Serializer Class for Ticket Comment model\n

    This is deprecated for now, and will not get any documentation\n

    """
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
    """
    Serializer Class for TicketStatus model\n

    The fields that are serialized on reads:\n
        1. id: pk for this record\n
        2. object_uuid: unique identifier for this record\n
        3. created: datetime when this record was created\n
        4. activated: datetime for when this record was activated\n
        5. deactivated: datetime for when this record was deactivated\n

    The fields that are serialized on writes:\n
        1. title

    """
    id = serializers.ReadOnlyField()
    object_uuid = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.TicketStatus
        fields = ["id",
                  "object_uuid",
                  "title", "created", "activated", "deactivated"]


class TicketTagSerializer(serializers.ModelSerializer):
    """
    Serializer Class for TicketTag model\n

    The fields that are serialized on reads:\n
        1. tag: serialized tag associated with this ticket tag\n
        2. object_uuid: unique id for this object\n
        3. created: when this ticket tag was created\n
        4. activated: when this ticket tag was activated\n
        5. deactivated: when this ticket tag was deactivated\n

    """
    tag = TagSerializer(many=False, read_only=True)
    object_uuid = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.TicketTag
        fields = ["tag", "created",
                  "object_uuid",
                  "activated", "deactivated"]


class TicketNodeSerializer(serializers.ModelSerializer):
    """
    Serializer Class for TicketNode model\n

    The fields that are serialized on reads:\n
        1. ticket_id: the pk for the associated ticket\n
    
    """
    ticket_id = serializers.ReadOnlyField()

    class Meta:
        model = api_models.TicketNode
        fields = ["ticket_id"]


class TicketSerializer(serializers.ModelSerializer):
    """
    Serializer Class for the Ticket model.\n

    The fields that are serialized on reads:\n
        1. id: pk of the ticket record\n
        2. team_id: pk of the associated team\n
        3. tag_list: serialized list of all tags\n
        4. owner: serialized user object which owns this ticket\n
        5. object_uuid: unique id for this object\n
        6. ticket_number: number for this ticket for the associated team\n
        7. comments: serialized list of comments (deprecated)\n
        8. assigned_user: serialized user object which is assigned to this ticket\n
        9. status: serialized status object associated with this ticket\n
        10. create: timestamp of creation date\n
        11. activated: timestamp of activation date\n
        12. deactivated: timestamp of deactivation date\n

    The fields that are serialized on writes:\n
        1. team_id: pk for the team with which to associate this ticket with (no affect on update)\n
        2. tag_id_list: list of pk which which to associate this ticket with\n
        3. parent_id: indicate the pk for a parent ticket\n
        4. assigned_user_id: indicate the user pk with which to assign this ticket to\n
    """

    id = serializers.ReadOnlyField()

    tag_list = PrimaryKeySerializedField(many=True, required=False,
                                         queryset=api_models.Tag.objects.all(), serializer=TagSerializer)

    parent_id = serializers.IntegerField(write_only=True, required=False)
    object_uuid = serializers.ReadOnlyField()

    owner = UserSerializer(many=False, read_only=True)
    ticket_number = serializers.ReadOnlyField()
    comments = TicketCommentSerializer(many=True, required=False)

    assigned_user = UserSerializer(many=False, read_only=True)

    status = PrimaryKeySerializedField(
        many=False, required=False, queryset=api_models.TicketStatus.objects.all(), serializer=TicketStatusSerializer
    )

    created = serializers.ReadOnlyField()
    activated = serializers.ReadOnlyField()
    deactivated = serializers.ReadOnlyField()

    class Meta:
        model = api_models.Ticket
        fields = [
            "id",
            "ticket_number",
            "tag_list",
            "parent_id",
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

        ticket = api_models.Ticket.objects.create(
            **validated_data
        )

        api_models.TicketTag.create_all(tag_list, ticket)

        return ticket

    # update the instance with validated_data
    def update(self, instance, validated_data):
        tag_list = validated_data.pop('tag_list', None)

        api_models.TicketTag.delete_difference(tag_list, instance)

        return super().update(instance, validated_data)


class EventSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    created = serializers.ReadOnlyField()
    event_type = serializers.ReadOnlyField()
    user = PrimaryKeySerializedField(
        many=False, queryset=api_models.Member.objects.all(), serializer=UserSerializer
    )
    description = serializers.ReadOnlyField()
    object_id = serializers.ReadOnlyField()

    class Meta:
        model = api_models.Event
        fields = [
            "id",
            "team_id",
            "created",
            "event_type",
            "user",
            "user_id",
            "description",
            "object_id"
        ]
