from django.contrib import admin
from .models import (Ticket, Member, Team, TicketComment, TicketStatus,
                     TicketNode, TicketTag, Event, Tag)


# Custom Admin class that will allow you to mark fields to be readonly on edits.
class customAdmin(admin.ModelAdmin):
    readonly_edit = tuple()

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Make team and owner readonly ONLY when the object already exists
            return self.readonly_fields + self.readonly_edit
        return self.readonly_fields


@admin.register(Event)
class EventAdmin(customAdmin):
    readonly_fields = ("object", "id")
    readonly_edit = ("team", )

    fields = ("id", "team", "event_type", "description", "user")


@admin.register(Member)
class MemberAdmin(customAdmin):
    readonly_fields = ("created", "id")
    readonly_edit = ("team", "owner")

    fields = ("id", "team", "owner", "role", "pronouns", "bio", "created",
              "activated", "deactivated")


@admin.register(Tag)
class TagAdmin(customAdmin):
    readonly_fields = ("team_title_hash", "id", "created")

    fields = ("id", "team", "title", "created", "activated", "deactivated",
              "team_title_hash")


@admin.register(Team)
class TeamAdmin(customAdmin):
    readonly_fields = ("created", "ticket_head", "id")

    fields = (("id", "ticket_head"), "name", "description", "created",
              "activated", "deactivated")


@admin.register(TicketComment)
class TicketCommentAdmin(customAdmin):
    readonly_fields = ("created", "id")
    readonly_edit = ("ticket", "team")

    fields = ("id", "team", "ticket", "owner", "content", "created",
              "activated", "deactivated")


@admin.register(TicketNode)
class TicketNodeAdmin(customAdmin):
    readonly_fields = ("id", )


@admin.register(TicketStatus)
class TicketStatusAdmin(customAdmin):
    readonly_fields = ("created", "id")
    readonly_edit = ("team", )

    fields = ("id", "team", "title", "created", "activated", "deactivated")


@admin.register(TicketTag)
class TicketTagAdmin(customAdmin):
    readonly_fields = ("created", "id")
    readonly_edit = ("team", )

    fields = ("id", "team", "tag", "ticket", "created", "activated",
              "deactivated")


@admin.register(Ticket)
class TicketAdmin(customAdmin):
    readonly_fields = ("created", "ticket_number", "id", "activated")
    readonly_edit = ("team", )

    fields = ("id", "ticket_number", "team", "owner", "assigned_user",
              "status", "title", "description", "created", "activated",
              "deactivated")
