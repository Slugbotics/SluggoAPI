from django.db import models
from .team import Team

from api.models.interfaces import HasUuid, TeamRelated


class TicketStatus(HasUuid, TeamRelated):
    """
    This model represents custom statuses that teams can set.
    By default, they will be created, started, and completed
    """

    title = models.CharField(max_length=100, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    activated = models.DateTimeField(null=True, blank=True)
    deactivated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        app_label = "api"

    def __str__(self):
        return f"TicketStatus: {self.title}"
