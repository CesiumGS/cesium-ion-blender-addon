APP_CATEGORY = "Cesium ion"
APP_OPERATOR_PREFIX = "csm"
APP_PACKAGE = __package__
LOCAL = False
if LOCAL:
    CLIENT_ID = "4"
    ION_ADDRESS = "http://composer.test:8081"
    API_ADDRESS = "http://api.composer.test:8081"
else:
    CLIENT_ID = "19"
    ION_ADDRESS = "https://cesium.com/ion"
    API_ADDRESS = "https://api.cesium.com"
REDIRECT_ADDRESS = "localhost"
REDIRECT_PORT = 10101
