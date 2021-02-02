from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

"""
assorted keys and 
"""

TEAM_PK = "team_pk"

TEAM_DETAIL_SCHEMA = dict(
    parameters=[
        OpenApiParameter(TEAM_PK, OpenApiTypes.INT, OpenApiParameter.PATH,
                         description="A unique integer value identifying this team.")
    ]
)

TEAM_LIST_SCHEME = dict(
    parameters=[
        OpenApiParameter(TEAM_PK, OpenApiTypes.INT, OpenApiParameter.PATH,
                         description="A unique integer value identifying this team."),
        OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY,
                         description="A search term used to filter the set"),
    ]
)
