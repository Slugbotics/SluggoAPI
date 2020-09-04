from django.db import models


class Team(models.Model):
    """
    this represents a team in sluggo
    """

    name = models.CharField(max_length=100, blank=False)
    description = models.TextField()
    ticket_head = models.IntegerField(blank=False, default=0)
    created = models.DateTimeField(auto_now_add=True)
    activated = models.DateTimeField(auto_now_add=True)
    deactivated = models.DateTimeField(blank=True)

    def __str__(self):
        return f"Team: {self.name}"
