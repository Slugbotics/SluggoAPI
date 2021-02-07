from django.db import models
from django.conf import settings

from .team import Team
from .ticket_status import TicketStatus
from api.models.interfaces import HasUuid, TeamRelated
import uuid


class Ticket(HasUuid, TeamRelated):
    """
    The Ticket class for Sluggo. This will store all information associated with a specific ticket.

    The class contains:
        owner: Foreign key to the creating user.
        assigned_user: Foreign key to an assigned user.
        title: Text field which is the title.
        team: inherited from TeamRelated, references a team
        status: foreign key to status object
        description: text field for a description
        created: creation datetime
        activated: activation date for the ticket
        deactivated: deactivation date for the ticket
    """

    ticket_number = models.IntegerField()

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name="owned_ticket",
                              null=False)

    assigned_user = models.ForeignKey(settings.AUTH_USER_MODEL,
                                      on_delete=models.CASCADE,
                                      related_name="assigned_ticket",
                                      null=True,
                                      blank=True)

    status = models.ForeignKey(TicketStatus,
                               on_delete=models.CASCADE,
                               related_name="status_ticket",
                               blank=True,
                               null=True)

    tag_list = models.ManyToManyField('Tag', through='TicketTag')

    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    activated = models.DateTimeField(auto_now_add=True)
    deactivated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        app_label = "api"

    @classmethod
    def retrieve_by_user(cls, user: settings.AUTH_USER_MODEL, team: Team):
        return cls.objects.filter(
            models.Q(team=team), models.Q(deactivated=None),
            models.Q(owner=user) | models.Q(assigned_user=user))

    def __str__(self):
        return f"Ticket: {self.title}"

    def save(self, *args, **kwargs):
        team = self.team
        owner = self.owner

        if not owner:
            raise ValueError("missing owner")

        if not team:
            raise ValueError("missing team")

        # id will be an md5 of the team.id formatted as a string, followed by the md5 of the username
        team.ticket_head += 1
        team.save()
        self.ticket_number = team.ticket_head

        super(Ticket, self).save(*args, **kwargs)