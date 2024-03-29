import sys
import traceback
import PlayFab.PlayFabErrors as PlayFabErrors


ProductionEnvironmentURL = ".playfabapi.com"

"""
The name of a customer vertical. This is only for customers running a private cluster. Generally you shouldn't touch this
"""
VerticalName = None

"""
You must set this value for PlayFabSdk to work properly (Found in the Game
Manager for your title, at the PlayFab Website)
"""

# TitleId = ""

if _DEVELOPMENT is False:
    TitleId = Mengine.getConfigString("Playfab", "TitleIDMaster", "")
else:
    TitleId = Mengine.getConfigString("Playfab", "TitleIDDev", "")

"""
You must set this value for Admin/Server/Matchmaker to work properly (Found in the Game
Manager for your title, at the PlayFab Website)
"""

DeveloperSecretKey = None

"""
Client specifics
"""

"""
Set this to the appropriate AD_TYPE_X constant below
"""
AdvertisingIdType = ""

"""
Set this to corresponding device value
"""
AdvertisingIdValue = None

"""
DisableAdvertising is provided for completeness, but changing it is not
suggested
Disabling this may prevent your advertising-related PlayFab marketplace
partners from working correctly
"""

DisableAdvertising = False
AD_TYPE_IDFA = "Idfa"
AD_TYPE_ANDROID_ID = "Adid"


class InternalSettings:
    pass


_internalSettings = InternalSettings()

"""
This is automatically populated by the PlayFabAuthenticationApi.GetEntityToken method.
"""
_internalSettings.EntityToken = None

"""
This is automatically populated by any PlayFabClientApi.Login method.
"""
_internalSettings.ClientSessionTicket = None
_internalSettings.SdkVersionString = "PythonSdk-0.0.181114"
_internalSettings.RequestGetParams = {
    "sdk": _internalSettings.SdkVersionString
}


def GetURL(methodUrl, getParams):
    if not TitleId:
        raise PlayFabErrors.PlayFabException("You must set PlayFabSettings.TitleId before making an API call")

    url = []
    if not ProductionEnvironmentURL.startswith("http"):
        if VerticalName:
            url.append("https://")
            url.append(VerticalName)
        else:
            url.append("https://")
            url.append(TitleId)

    url.append(ProductionEnvironmentURL)
    url.append(methodUrl)

    if getParams:
        for idx, (k, v) in enumerate(getParams.items()):
            if idx == 0:
                url.append("?")
            else:
                url.append("&")
            url.append(k)
            url.append("=")
            url.append(v)

    return "".join(url)


def DefaultExceptionLogger(exceptionObj):
    print("Unexpected error:", sys.exc_info()[0])
    traceback.print_exc()


def MengineExceptionLogger(exceptionObj):
    Trace.log("PlayFab", 0, "[PlayFab-PythonSDK] Exception:\n> {}".format(exceptionObj))


GlobalErrorHandler = None
GlobalExceptionLogger = MengineExceptionLogger
