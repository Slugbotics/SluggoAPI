# this here defines the ticket_tags
from django.db import models
import uuid
from .team import Team
from .ticket import Ticket
from api.models.interfaces import HasUuid, TeamRelated
from hashlib import md5


class Tag(HasUuid, TeamRelated):
    team_title_hash = models.CharField(max_length=256,
                                       unique=True,
                                       editable=False)
    title = models.CharField(max_length=100, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    activated = models.DateTimeField(null=True, blank=True)
    deactivated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        app_label = "api"

    def __str__(self):
        return f"Tag: {self.title}"

    def save(self, *args, **kwargs):
        team = self.team
        title = self.title

        if not title:
            raise ValueError("missing title")

        if not team:
            raise ValueError("missing team")

        title_id = "{}".format(title)
        team_id = "{}".format(team.id)
        self.team_title_hash = md5(title_id.encode()).hexdigest() + md5(
            team_id.encode()).hexdigest()

        super(Tag, self).save(*args, **kwargs)


class TicketTag(HasUuid, TeamRelated):
    id = models.CharField(max_length=256,
                          unique=True,
                          editable=False,
                          primary_key=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    activated = models.DateTimeField(null=True, blank=True)
    deactivated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created"]
        app_label = "api"

    @classmethod
    def create_all(cls, tag_list: list, ticket: Ticket):
        if not tag_list:
            return

        for tag in tag_list:
            cls.objects.create(tag=tag, ticket=ticket, team=ticket.team)

    @classmethod
    def delete_difference(cls, tag_list: list, ticket_instance: Ticket):
        if not tag_list or len(tag_list) <= 0:
            return

        filters = models.Q(tag=tag_list.pop(0))
        for tag in tag_list:
            filters |= models.Q(tag=tag)

        # select all that are not in the tag list
        to_be_deleted = cls.objects.filter(
            ticket=ticket_instance).exclude(filters)
        if to_be_deleted:
            for ticket_tag in to_be_deleted:
                ticket_tag.delete()

        for tag in tag_list:
            cls.objects.get_or_create(ticket=ticket_instance,
                                      tag=tag,
                                      team=ticket_instance.team)

    def __str__(self):
        return f"TicketTag: {self.created}"

    def save(self, *args, **kwargs):
        tag = self.tag
        ticket = self.ticket

        if not tag:
            raise ValueError("missing tag")

        if not ticket:
            raise ValueError("missing ticket")

        team_id = "{}".format(tag.id)
        ticket_id = "{}".format(ticket.id)
        self.id = md5(team_id.encode()).hexdigest() + md5(
            ticket_id.encode()).hexdigest()

        super(TicketTag, self).save(*args, **kwargs)
