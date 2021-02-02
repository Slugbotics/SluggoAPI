from django.contrib import admin
from .models import (
    Ticket, Member, Team, TicketComment, TicketStatus, TicketNode, TicketTag, Event
)


class TicketAdmin(admin.ModelAdmin):
    readonly_fields = ("created",)


# Register your models here.
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Member)
admin.site.register(Team)
admin.site.register(TicketComment)
admin.site.register(TicketStatus)
admin.site.register(TicketNode)
admin.site.register(TicketTag)
admin.site.register(Event)
