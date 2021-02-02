from rest_framework.schemas import get_schema_view
from django.urls import include, path
from django.contrib import admin
from rest_framework.routers import DefaultRouter, SimpleRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_nested import routers

from . import views

router = SimpleRouter()
router.register('teams', views.TeamViewSet)

team_router = routers.NestedSimpleRouter(
    router,
    r'teams',
    lookup='team'
)

team_router.register(
    r'tickets',
    views.TicketViewSet,
    basename='team-tickets'
)

team_router.register(
    r'members',
    views.MemberViewSet,
    basename='team-members'
)

team_router.register(
    r'statuses',
    views.StatusViewSet,
    basename='team-statuses'
)

team_router.register(
    r'tags',
    views.TagViewSet,
    basename='team-tags'
)

team_router.register(
    r'events',
    views.EventViewSet,
    basename='team-events'
)

urlpatterns = [
    # Optional UI:
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path("api/", include(router.urls)),
    path("api/", include(team_router.urls)),

    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/slack/', views.SlackLogin.as_view(), name="slack_login"),

    path('auth/accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls)
]
