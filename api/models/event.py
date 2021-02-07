from django.db import models
from .team import Team
from django.conf import settings
import uuid

from api.models.interfaces import HasUuid, TeamRelated


class Event(TeamRelated):
    CREATE = 1
    UPDATE = 2
    DELETE = 3

    events = [
        (CREATE, "Create"),
        (UPDATE, "Update"),
        (DELETE, "Delete"),
    ]

    created = models.DateTimeField(auto_now_add=True)
    event_type = models.SmallIntegerField(choices=events)
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             null=True,
                             blank=True,
                             on_delete=models.SET_NULL)
    object = models.UUIDField(null=True, blank=False, default=uuid.uuid4)

    def is_create(self):
        return self.CREATE == self.event_type

    def is_update(self):
        return self.UPDATE == self.event_type

    def is_delete(self):
        return self.DELETE == self.event_type

    class Meta:
        ordering = ["-created"]
        app_label = "api"

    def __str__(self):
        return f"Event: {self.event_type}, {self.description}"

