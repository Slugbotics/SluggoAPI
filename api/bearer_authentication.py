from rest_framework.authentication import TokenAuthentication


class BearerAuthentication(TokenAuthentication):
    """
    Override the expected keyword to Bearer in order to play nicely with postman
    """
    keyword = "Bearer"
