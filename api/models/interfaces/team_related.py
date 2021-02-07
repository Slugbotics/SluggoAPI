from django.db import models
from ..team import Team


class TeamRelated(models.Model):
    team = models.ForeignKey(Team,
                             on_delete=models.CASCADE,
                             editable=True,
                             null=False)

    class Meta:
        app_label = "api"
        abstract = True
