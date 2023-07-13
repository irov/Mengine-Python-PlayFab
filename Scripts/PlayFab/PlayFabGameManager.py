from Foundation.DefaultManager import DefaultManager
from Foundation.Manager import Manager
from PlayFab.PlayFabManager import PlayFabManager


# todo: replace with PlayFab player data params
STUFF_CELL_INDEX_START = 1
ITEMS_MAX_COUNT = 3
BOOSTERS_MAX_COUNT = 4

# server status
SERVER_STATUS_OK = 0
SERVER_STATUS_FAIL = 1
SERVER_STATUS_UPDATING = 2


class GameManager(Manager):
    s_player_data_cache = {}

    @staticmethod
    def getLoadDataCache(tag):
        return GameManager.s_player_data_cache.get(tag)

    @staticmethod
    def setLoadDataCache(tag, data):
        GameManager.s_player_data_cache[tag] = data

    @staticmethod
    def clearLoadDataCache():
        GameManager.s_player_data_caTaskTransitionche = {}

    @staticmethod
    def getDefaultPlayerName():
        return '{}'.format(Mengine.getTimeMs())

    @staticmethod
    def makeId(id=None):
        if id is None:
            id = Mengine.rand(100)

        text = ""
        possible = "QjVGEOLeKUXPNp0iFy7l1TYoIDAd3usH8wgWf5nChtqvbaZScBm2JM6rkR4xz9"

        for i in range(8):
            text += possible[((id >> (i * 4)) & 0xF) + i]
            text += possible[Mengine.rand(len(possible))]

        return text

    @staticmethod
    def getDefaultPassword():
        return GameManager.makeId()

    @staticmethod
    def scopeDefaultRegistration(source, success_cb, fail_cb, **error_handlers):
        # print "PLAYFAB scopeDefaultRegistration"

        default_name = GameManager.getDefaultPlayerName()
        default_password = GameManager.getDefaultPassword()

        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            Mengine.changeCurrentAccountSetting("FirstLogin", u'False')
            Mengine.changeCurrentAccountSetting("PlayFabId", response.get("PlayFabId"))
            return response

        source.addScope(
            PlayFabManager.scopeRegisterPlayFabUser,
            default_name, default_password,
            __success_cb, fail_cb, **error_handlers)

        if Mengine.hasTouchpad():
            android_id = Mengine.getAndroidId()
            source.addScope(GameManager.scopeLinkAndroidDeviceID, android_id, False)

    @staticmethod
    def scopeLinkAndroidDeviceID(source, android_device_id, force_link, isSuccessHolder=None):
        def __success_cb(response):
            Mengine.saveAccounts()
            if isSuccessHolder is not None:
                isSuccessHolder.setValue(True)

            return response

        def __error(func):
            def __wrapper(*args, **kwargs):
                func(*args, **kwargs)

                if isSuccessHolder is not None:
                    isSuccessHolder.setValue(False)

            return __wrapper

        @__error
        def __fail_cb(playFabError):
            Mengine.logError("[PlayFab] LinkAndroidDeviceID fail: {}".format(playFabError))

        error_handlers = dict(
            LinkedDeviceAlreadyClaimed=__fail_cb,
        )

        source.addScope(
            PlayFabManager.scopeLinkAndroidDeviceID,
            android_device_id, force_link,
            __success_cb, __fail_cb, **error_handlers)

    @staticmethod
    def scopeUnLinkAndroidDeviceID(source, android_device_id, isSuccessHolder=None):
        def __success_cb(response):
            if isSuccessHolder is not None:
                isSuccessHolder.setValue(True)

            return response

        def __error(func):
            def __wrapper(*args, **kwargs):
                func(*args, **kwargs)

                if isSuccessHolder is not None:
                    isSuccessHolder.setValue(False)

            return __wrapper

        @__error
        def __fail_cb(playFabError):
            Mengine.logError("[PlayFab] UnLinkAndroidDeviceID fail: {}".format(playFabError))

        error_handlers = dict(
            AccountNotLinked=__fail_cb,
            DeviceNotLinked=__fail_cb,
        )

        source.addScope(
            PlayFabManager.scopeUnLinkAndroidDeviceID,
            android_device_id,
            __success_cb, __fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginWithAndroidDeviceID(source, android_device_id, isSuccessHolder=None, __cb=None):
        if android_device_id is None:
            return

        def __success_cb(response):
            print('scopeLoginWithAndroidDeviceID.__success_cb')
            Mengine.changeCurrentAccountSetting("FirstLogin", u'False')
            Mengine.changeCurrentAccountSetting("PlayFabId", response.get("PlayFabId"))

            Mengine.saveAccounts()

            if isSuccessHolder is not None:
                isSuccessHolder.setValue(True)

            if __cb is not None:
                __cb(response)

            return response

        def __error(func):
            print('scopeLoginWithAndroidDeviceID.__error')

            def __wrapper(*args, **kwargs):
                func(*args, **kwargs)

                if isSuccessHolder is not None:
                    isSuccessHolder.setValue(False)

            return __wrapper

        @__error
        def __fail_cb(playFabError):
            Mengine.logError("[PlayFab] LoginWithAndroidDeviceID fail: {}".format(playFabError))

        def __account_not_found_cb(playFabError):
            Mengine.logWarning("[PlayFab] LoginWithAndroidDeviceID not found account - start create account! {}".format(playFabError))

        error_handlers = dict(
            AccountNotFound=__account_not_found_cb,
            EncryptionKeyMissing=__fail_cb,
            EvaluationModePlayerCountExceeded=__fail_cb,
            InvalidSignature=__fail_cb,
            InvalidSignatureTime=__fail_cb,
            PlayerSecretAlreadyConfigured=__fail_cb,
            PlayerSecretNotConfigured=__fail_cb,
            RequestViewConstraintParamsNotAllowed=__fail_cb,
        )
        source.addPrint('scopeLoginWithAndroidDeviceID before')
        source.addScope(
            PlayFabManager.scopeLoginWithAndroidDeviceID,
            android_device_id,
            __success_cb, __fail_cb, **error_handlers)
        source.addPrint('scopeLoginWithAndroidDeviceID after')

    @staticmethod
    def scopeAuthenticate(source, isSuccessHolder=None):
        def __error(func):
            def __wrapper(*args, **kwargs):
                func(*args, **kwargs)

                if isSuccessHolder is not None:
                    isSuccessHolder.setValue(False)

            return __wrapper

        def __success_cb(response):
            Mengine.saveAccounts()
            holder_login_success.set(True)
            if isSuccessHolder is not None:
                isSuccessHolder.setValue(True)

        @__error
        def __fail_cb(playFabError):
            Mengine.logError("[PlayFab] Authenticate fail: {}".format(playFabError))

        def __account_not_found_cb(playFabError):
            Mengine.logWarning("[PlayFab] LoginWithAndroidDeviceID not found account - start create account! {}".format(playFabError))
            holder_login_success.set(False)

        isFirstLogin = Mengine.getCurrentAccountSettingBool("FirstLogin")

        error_handlers = dict(
            AccountNotFound=__account_not_found_cb,
            InvalidEmailOrPassword=__fail_cb,
            InvalidUsernameOrPassword=__fail_cb,
            InvalidTitleId=__fail_cb,
            RequestViewConstraintParamsNotAllowed=__fail_cb,
        )

        isFirstLogin = Mengine.getCurrentAccountSettingBool("FirstLogin")

        android_device_id = None
        if Mengine.hasTouchpad():
            android_device_id = Mengine.getAndroidId()
        semaphore_android_login = Semaphore(False, "AndroidLogin")
        holder_login_success = Holder()

        with source.addIfTask(lambda: isFirstLogin is True) as (source_first_login, source_not_first_login):
            # fl == first login, nfl == not first login
            with source_first_login.addIfTask(lambda: _ANDROID is True) as (fl_android, fl_not_android):
                fl_android.addScope(GameManager.scopeLoginWithAndroidDeviceID,
                                    android_device_id, semaphore_android_login, __success_cb)

                with fl_android.addRaceTask(2) as (fl_android_success_login, fl_android_fail_login):
                    fl_android_success_login.addSemaphore(semaphore_android_login, From=True)
                    fl_android_success_login.addPrint('GameManager.scopeLoginWithAndroidDeviceID True fl')

                    fl_android_fail_login.addDelay(10000)  # wait response from playfab login with android device id
                    fl_android_fail_login.addPrint('GameManager.scopeLoginWithAndroidDeviceID time fl')

                    fl_android_fail_login.addScope(GameManager.scopeDefaultRegistration,
                                                   __success_cb, __fail_cb, **error_handlers)

                fl_not_android.addScope(GameManager.scopeDefaultRegistration,
                                        __success_cb, __fail_cb, **error_handlers)

            with source_not_first_login.addIfTask(lambda: _ANDROID is True) as (nfl_android, nfl_not_android):
                nfl_android.addScope(GameManager.scopeLoginWithAndroidDeviceID,
                                     android_device_id, semaphore_android_login, __success_cb)

                with nfl_android.addRaceTask(2) as (nfl_android_success_login, nfl_android_fail_login):
                    nfl_android_success_login.addSemaphore(semaphore_android_login, From=True)
                    nfl_android_success_login.addPrint('GameManager.scopeLoginWithAndroidDeviceID True nfl')

                    nfl_android_fail_login.addDelay(10000)  # wait response from PlayFab login with android device id
                    nfl_android_fail_login.addPrint('GameManager.scopeLoginWithAndroidDeviceID time nfl')
                    # next string causes bug on Android with MarSDK
                    # nfl_android_fail_login.addPrint('Name PSW {} {}'.format(Mengine.getCurrentAccountSetting("Name"), Mengine.getCurrentAccountSetting("Password")))

                    nfl_android_fail_login.addScope(PlayFabManager.scopeLoginWithPlayFab,
                                                    Mengine.getCurrentAccountSetting("Name"),
                                                    Mengine.getCurrentAccountSetting("Password"),
                                                    __success_cb, __fail_cb, **error_handlers)

                    # pf == PlayFab
                    with nfl_android_fail_login.addIfTask(lambda: nfl_android_fail_login is True) as (pf_login_success, pf_login_fail):
                        pf_login_fail.addScope(GameManager.scopeDefaultRegistration,
                                               __success_cb, __fail_cb, **error_handlers)

                nfl_not_android.addScope(PlayFabManager.scopeLoginWithPlayFab,
                                         Mengine.getCurrentAccountSetting("Name"),
                                         Mengine.getCurrentAccountSetting("Password"),
                                         __success_cb, __fail_cb, **error_handlers)
        source.addPrint('Login finish')

    @staticmethod
    def scopeGetAccountInfo(source, isSuccessHolder=None):
        def __error(func):
            def __wrapper(*args, **kwargs):
                func(*args, **kwargs)

                if isSuccessHolder is not None:
                    isSuccessHolder.setValue(False)

            return __wrapper

        def __success_cb(account_info):
            Mengine.saveAccounts()

            GameManager.setLoadDataCache("AccountInfo", account_info)

            if isSuccessHolder is not None:
                isSuccessHolder.setValue(True)

        @__error
        def __fail_cb(playFabError):
            Mengine.logError("[PlayFab] GetAccountInfo fail: {}".format(playFabError))

        error_handlers = dict(
            AccountNotFound=__fail_cb,
        )

        source.addScope(
            PlayFabManager.scopeGetAccountInfo,
            __success_cb, __fail_cb, **error_handlers)

    @staticmethod
    def scopeUpdatePlayerStatistics(source, score):
        statistic_name = DefaultManager.getDefault("DefaultLeaderboardStatisticName", "general_score")

        statistics = [
            {
                "StatisticName": statistic_name,
                "Value": score
            }
        ]

        def __success_cb(response):
            print("updatePlayerStatistics __success_cb", statistics)

        def __fail_cb(playFabError):
            Mengine.logError("[PlayFab] UpdatePlayerStatistics fail: {}".format(playFabError))

        error_handlers = {
            "AccountNotFound": __fail_cb,
            "APINotEnabledForGameClientAccess": __fail_cb,
            "DuplicateStatisticName": __fail_cb,
            "StatisticCountLimitExceeded": __fail_cb,
            "StatisticNameConflict": __fail_cb,
            "StatisticNotFound": __fail_cb,
            "StatisticValueAggregationOverflow": __fail_cb,
            "StatisticVersionClosedForWrites": __fail_cb,
            "StatisticVersionInvalid": __fail_cb,
            "ServiceUnavailable": __fail_cb,
        }

        source.addScope(PlayFabManager.scopeUpdatePlayerStatistics, statistics,
                        __success_cb, __fail_cb, **error_handlers)

    @staticmethod
    def scopeLoadStatistics(source, isSuccessHolder=None):
        statistic_name = DefaultManager.getDefault("DefaultLeaderboardStatisticName", "general_score")

        statistic_names = [
            statistic_name
        ]

        def __success_cb(statistics):
            GameManager.setLoadDataCache("Statistics", statistics)
            if isSuccessHolder is not None:
                isSuccessHolder.setValue(True)

        def __fail_cb(playFabError):
            Mengine.logError("[PlayFab] GetPlayerStatistics fail: {}".format(playFabError))
            if isSuccessHolder is not None:
                isSuccessHolder.setValue(False)

        error_handlers = dict(
            # no possible error handlers noted in playfab documentation
        )

        source.addScope(
            PlayFabManager.scopeGetPlayerStatistics,
            statistic_names,
            __success_cb, __fail_cb, **error_handlers)

    @staticmethod
    def scopeVersionCheckAndLoadPlayer(source, isSuccessHolder=None):   # deprecated
        keys = ["Bank", "Quests", "Store"]

        def __success_cb(data):
            # server_status = data.get("ServerStatus")

            # if server_status is not SERVER_STATUS_OK:
            #     if server_status is SERVER_STATUS_FAIL:
            #         print "EEEEEEEEEEEEEEEEEEEEEEEE SERVER FAIL EEEEEEEEEEEEEEEEEEEEEEEEEEEE"
            #         Notification.notify(Notificator.onMessageOkPopUp, "ServerFail")
            #     elif server_status is SERVER_STATUS_UPDATING:
            #         Notification.notify(Notificator.onMessageOkPopUp, "ServerUpdating")
            #
            #         print "EEEEEEEEEEEEEEEEEEEEEEEE SERVER IS UPDATING EEEEEEEEEEEEEEEEEEEEEEEEEEEE"
            #
            #     if isSuccessHolder is not None:
            #         isSuccessHolder.set(True)
            #     return
            #
            # player_data = data.get("PlayerData")
            #
            # if player_data is None:
            #     print "PPPPPPPPPPPPPPPPPPPPPPPPP PLAYER DATA IS EMPTY PPPPPPPPPPPPPPPPPPPPPPPPP"
            #     Notification.notify(Notificator.onMessageOkPopUp, "ServerFail")
            #     if isSuccessHolder is not None:
            #         isSuccessHolder.set(True)
            #     return

            if GameManager.checkProjectVersion(data) is False:
                print("VVVVVVVVVVVVVVVVVVVVVV PROJECT VERSION IS NOT VALID VVVVVVVVVVVVVVVVVVVVVVV")
                from Game.PopUp import PopUp
                source.addScope(PopUp.scope_Check_Version)
                # Notification.notify(Notificator.onMessageOkPopUp, "AppUpdate")
                if isSuccessHolder is not None:
                    isSuccessHolder.set(False)
                return

            # # check all requested keys
            # for playerDataKey in keys:
            #     if playerDataKey not in player_data:
            #         if isSuccessHolder is not None:
            #             isSuccessHolder.set(False)
            #         return
            #
            # # NewSaveManager.setLoadDataCache("PlayerData", player_data)

            if isSuccessHolder is not None:
                isSuccessHolder.set(True)

        def __fail_cb(playFabError):
            Mengine.logError("[PlayFab] API_OnPlayerLoggedIn fail: {}".format(playFabError))
            Notification.notify(Notificator.onInternetConnectionLost)

            if isSuccessHolder is not None:
                isSuccessHolder.set(False)

        error_handlers = {
            "CloudScriptAPIRequestCountExceeded": __fail_cb,
            "CloudScriptAPIRequestError": __fail_cb,
            "CloudScriptFunctionArgumentSizeExceeded": __fail_cb,
            "CloudScriptHTTPRequestError": __fail_cb,
            "CloudScriptNotFound": __fail_cb,
            "JavascriptException": __fail_cb,
        }

        source.addScope(
            PlayFabManager.scopeExecuteCloudScript,
            "API_OnPlayerLoggedIn",
            {
                "__api_version__": 1
            },
            __success_cb, __fail_cb, **error_handlers)

    @staticmethod
    def checkProjectVersion(data):
        server_project_version_string = data.get("ProjectVersion")

        if server_project_version_string is None:
            print("NO PROJECT VERSION IN ON LOGGED IN RESPONSE")
            return False

        client_project_version = Mengine.getConfigInt("Playfab", "ProjectVersion", 0)

        # dirty hack
        server_project_version_parts = server_project_version_string.split(".")
        if not server_project_version_parts:
            print("PROJECT VERSION FAIL TO CONVERT")
            return False

        server_project_version = int(server_project_version_parts[0])

        print()
        print(" ___PROJECT_VERSION___ SERVER='{}' / CLIENT='{}'".format(server_project_version, client_project_version))

        is_valid_versions = server_project_version <= client_project_version

        print(" __CHECK__ {}".format(is_valid_versions))

        return is_valid_versions

    @staticmethod
    def scopeLoadTitleDataFromServer(source, isSuccessHolder=None, PrintTitleData=False, PrintRevision=True):
        PrintRevision = True

        title_data_keys = ["ProjectVersion"]

        def __success_cb(data):
            if len(data) == 0:  # try again
                print(" DATA IS EMPTY - TRY AGAIN ".center(100, "A"))
                if isSuccessHolder is not None:
                    isSuccessHolder.setValue(False)
                return
            if GameManager.checkProjectVersion(data) is False:
                print(" checkProjectVersion is False ".center(100, "A"))
                if isSuccessHolder is not None:
                    isSuccessHolder.setValue(False)
                return

            if isSuccessHolder is not None:
                isSuccessHolder.setValue(True)

        def __fail_cb(playFabError):
            Mengine.logError("[PlayFab] GetTitleData fail: {}".format(playFabError))

            if isSuccessHolder is not None:
                isSuccessHolder.setValue(False)

        error_handlers = dict(
            # no possible error handlers noted in playfab documentation
        )

        source.addScope(
            PlayFabManager.scopeGetTitleData,
            title_data_keys,
            __success_cb, __fail_cb, **error_handlers)
