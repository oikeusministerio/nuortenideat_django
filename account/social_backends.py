from social.backends.instagram import InstagramOAuth2


class InstagramBackend(InstagramOAuth2):
    # without REDIRECT STATE = False sign up does not work if instagram user is not
    # logged in
    REDIRECT_STATE = False
