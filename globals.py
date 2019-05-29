APP_CATEGORY = "Cesium ion"
APP_OPERATOR_PREFIX = "csm"
APP_PACKAGE = __package__
LOCAL = True
if LOCAL:
    CLIENT_ID = "4"
    ION_ADDRESS = "http://composer.test:8081"
    API_ADDRESS = "http://api.composer.test:8081"
else:
    pass  # TODO -- ADD INFO
REDIRECT_ADDRESS = "localhost"
REDIRECT_PORT = 10101
