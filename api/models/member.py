from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from hashlib import md5
import uuid

from api.models.interfaces import HasUuid, TeamRelated
from .team import Team

User = get_user_model()


class Member(HasUuid, TeamRelated):
    """
    The Ticket class for Sluggo. This will store all information associated with a specific ticket.

    The class contains:
        owner: A foreign key to a specific user that authored the ticket. Allows for them to edit the ticket.
        assigned_user: A foreign key that refers to a specific user that the ticket is assigned to.
        title: A char field for the title of the ticket (currently limited to 100 characters and is a required field).
        description: A multiline text field that will store the longer form explanation of the ticket.
        created: A datetime field that will record when a ticket has been made.
        started: A ticket can be made before anyone actually starts it, so the started field must be seperate. (Also datetime)
        completed: A field to record when a ticket has been finished. (Datetime as well)
        due_date: The due date for the ticket, a date field that will keep track of when things are due.
    """
    class Roles(models.TextChoices):
        """
        A private class containing 3 options for Roles stored in multiple versions. A full name, "pretty" name, and 2-letter representation.

        The options are:
            Unapproved: Roles.UNAPPROVED, Roles['UNAPPROVED'] or Roles('UA')
            Approved: Roles.APPROVED, Roles['APPROVED'] or Roles('AP')
            Admin: Roles.ADMIN, Roles['ADMIN'] or Roles('AD')
        """

        UNAPPROVED = "UA", _("Unapproved")
        APPROVED = "AP", _("Approved")
        ADMIN = "AD", _("Admin")

    # team.team_id + md5 (user.username)
    id = models.CharField(max_length=256,
                          unique=True,
                          editable=False,
                          primary_key=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              editable=True)

    role = models.CharField(max_length=2,
                            choices=Roles.choices,
                            default=Roles.UNAPPROVED)

    pronouns = models.CharField(max_length=256, null=True, blank=True)

    bio = models.TextField(default="", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    activated = models.DateTimeField(null=True, blank=True)
    deactivated = models.DateTimeField(null=True, blank=True)

    def is_admin(self):
        return self.role == self.Roles.ADMIN

    def is_approved(self):
        return self.role == self.Roles.ADMIN or self.role == self.Roles.APPROVED

    @classmethod
    def get_member(cls, user, team: Team):
        team_id = team.id
        team_id = "{}".format(team_id)
        username = user.username
        member_pk = (md5(team_id.encode()).hexdigest() +
                     md5(username.encode()).hexdigest())
        return Member.objects.get(pk=member_pk)

    class Meta:
        ordering = ["created"]
        app_label = "api"

    def __str__(self):
        return f"Member: {self.owner.get_full_name}"

    def save(self, *args, **kwargs):
        team = self.team
        owner = self.owner

        if not owner:
            raise ValueError("missing owner")

        if not team:
            raise ValueError("missing team")

        # id will be an md5 of the team.id formatted as a string, followed by the md5 of the username

        team_id = "{}".format(team.id)
        self.id = md5(team_id.encode()).hexdigest() + md5(
            owner.username.encode()).hexdigest()

        super(Member, self).save(*args, **kwargs)
