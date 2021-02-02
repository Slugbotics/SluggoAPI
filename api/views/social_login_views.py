from allauth.socialaccount.providers.slack.views import SlackOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView


class SlackLogin(SocialLoginView):
    """
    Slack endpoints. Only access_token is the concern. Use /slack/ to authenticate the client with a slack token.
    A token for this app will be returned.
    """
    adapter_class = SlackOAuth2Adapter
