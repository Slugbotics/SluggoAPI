from django.db import models
from api.models.interfaces import HasUuid


class Team(HasUuid):
    # id is implicitly defined by django
    name = models.CharField(max_length=100, unique=True, blank=False)
    ticket_head = models.IntegerField(blank=False, default=0, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    activated = models.DateTimeField(null=True, blank=True)
    deactivated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created"]
        app_label = "api"

    def __str__(self):
        return f"Team: {self.id}, {self.name}"
