from Foundation.DefaultManager import DefaultManager
from Foundation.Manager import Manager
from Foundation.TaskManager import TaskManager
from PlayFab.PlayFabErrors import PlayFabError
import PlayFab.PlayFabClientAPI as PlayFabClientAPI
import PlayFab.PlayFabSettings as PlayFabSettings


class PlayFabManager(Manager):
    GOOGLE_GAME_SOCIAL_PLUGIN = "AndroidGGameSocialPlugin"
    IOS_GAME_CENTER_PLUGIN = "iOSGameCenterPlugin"
    PLATFORM_IDENTITY_TIMEOUT_TASK = "PlayFabPlatformIdentityTimeout"

    timestamps_queue = []
    s_debug_pretty_print = False

    s_identity_linking_initialized = False
    s_android_callback_ids = []
    s_custom_id_link_in_progress = False
    s_custom_id_link_attempted = False
    s_platform_link_in_progress = False
    s_platform_link_attempted = False
    s_platform_identity_request_sequence = 0
    s_platform_identity_request_id = None
    s_platform_identity_success_cb = None
    s_platform_identity_error_cb = None
    s_platform_identity_canceled_cb = None

    # = DEBUG ===========================================================================================================
    @staticmethod
    def print_data(msg, data):
        DebugPlayFabResponseDataPrint = DefaultManager.getDefaultBool("DebugPlayFabResponseDataPrint", False)

        if isinstance(data, PlayFabError) is False and PlayFabManager.s_debug_pretty_print is True:
            data = Mengine.encodeJSON(data, indent=2)

        LINE_CHAR_COUNT = 79
        Trace.msg("\n" + " {} ".format(msg).center(LINE_CHAR_COUNT, '#'))

        if DebugPlayFabResponseDataPrint is True:
            Trace.msg(data)
        else:
            Trace.msg("! PlayFab response data print is disabled.")
            Trace.msg("! For enable change default param 'DebugPlayFabResponseDataPrint' to True")

        Trace.msg("".center(LINE_CHAR_COUNT, '#') + "\n")

    # = INIT ============================================================================================================
    @staticmethod
    def _onInitialize(*args):
        PlayFabManager.s_debug_pretty_print = DefaultManager.getDefaultBool("DebugDataPrettyPrint", False)

        PlayFabManager.initializeIdentityLinking()

    @staticmethod
    def initializeIdentityLinking():
        if PlayFabManager.s_identity_linking_initialized is True:
            return

        PlayFabManager.s_identity_linking_initialized = True

        if _ANDROID is True and Mengine.isAvailablePlugin(PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN) is True:
            success_callback_id = Mengine.addAndroidCallback(
                PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN,
                "onGoogleGameSocialRequestServerAuthCodeSuccess",
                PlayFabManager.__onGooglePlayGamesServerAuthCodeSuccess)
            error_callback_id = Mengine.addAndroidCallback(
                PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN,
                "onGoogleGameSocialRequestServerAuthCodeError",
                PlayFabManager.__onGooglePlayGamesServerAuthCodeError)
            canceled_callback_id = Mengine.addAndroidCallback(
                PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN,
                "onGoogleGameSocialRequestServerAuthCodeCanceled",
                PlayFabManager.__onGooglePlayGamesServerAuthCodeCanceled)

            PlayFabManager.s_android_callback_ids = [
                ("onGoogleGameSocialRequestServerAuthCodeSuccess", success_callback_id),
                ("onGoogleGameSocialRequestServerAuthCodeError", error_callback_id),
                ("onGoogleGameSocialRequestServerAuthCodeCanceled", canceled_callback_id),
            ]

            Mengine.waitSemaphore("GoogleGameSocialAuthenticated", PlayFabManager.ensureIdentityLinks)

        if _IOS is True and Mengine.isAvailablePlugin(PlayFabManager.IOS_GAME_CENTER_PLUGIN) is True:
            Mengine.waitSemaphore("GameCenterAuthenticated", PlayFabManager.ensureIdentityLinks)

    @staticmethod
    def finalizeIdentityLinking():
        if _ANDROID is True:
            for callback_name, callback_id in PlayFabManager.s_android_callback_ids:
                Mengine.removeAndroidCallback(
                    PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN,
                    callback_name,
                    callback_id)

        PlayFabManager.s_android_callback_ids = []
        PlayFabManager.s_identity_linking_initialized = False
        PlayFabManager.__clearPlatformIdentityRequest()
        PlayFabManager.__resetIdentityLinkState()

    @staticmethod
    def __resetIdentityLinkState():
        PlayFabManager.s_custom_id_link_in_progress = False
        PlayFabManager.s_custom_id_link_attempted = False
        PlayFabManager.s_platform_link_in_progress = False
        PlayFabManager.s_platform_link_attempted = False

    @staticmethod
    def __cancelPlatformIdentityTimeout():
        if TaskManager.existTaskChain(PlayFabManager.PLATFORM_IDENTITY_TIMEOUT_TASK) is True:
            TaskManager.cancelTaskChain(PlayFabManager.PLATFORM_IDENTITY_TIMEOUT_TASK, exist=False)

    @staticmethod
    def __clearPlatformIdentityRequest(cancel_timeout=True):
        if cancel_timeout is True:
            PlayFabManager.__cancelPlatformIdentityTimeout()

        PlayFabManager.s_platform_identity_request_id = None
        PlayFabManager.s_platform_identity_success_cb = None
        PlayFabManager.s_platform_identity_error_cb = None
        PlayFabManager.s_platform_identity_canceled_cb = None

    @staticmethod
    def __completePlatformIdentityRequest(request_id, status, payload=None, cancel_timeout=True):
        if request_id != PlayFabManager.s_platform_identity_request_id:
            Trace.msg_dev("[PlayFab] Ignored stale platform identity callback")
            return False

        success_cb = PlayFabManager.s_platform_identity_success_cb
        error_cb = PlayFabManager.s_platform_identity_error_cb
        canceled_cb = PlayFabManager.s_platform_identity_canceled_cb

        PlayFabManager.__clearPlatformIdentityRequest(cancel_timeout)

        if status == "Success":
            success_cb(payload)
        elif status == "Canceled":
            canceled_cb(payload)
        else:
            error_cb(payload)

        return True

    @staticmethod
    def __onPlatformIdentityTimeout(request_id):
        PlayFabManager.__completePlatformIdentityRequest(
            request_id,
            "Error",
            "Timeout",
            cancel_timeout=False)

    @staticmethod
    def isPlatformIdentitySupported():
        if _ANDROID is True:
            return Mengine.isAvailablePlugin(PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN)

        if _IOS is True:
            return Mengine.isAvailablePlugin(PlayFabManager.IOS_GAME_CENTER_PLUGIN)

        return False

    @staticmethod
    def __startPlatformIdentityRequest(request_id, provider):
        if request_id != PlayFabManager.s_platform_identity_request_id:
            Trace.msg_dev("[PlayFab] Ignored stale platform identity start")
            return False

        if provider == "GooglePlayGames":
            if Mengine.androidBooleanMethod(PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN, "isAuthenticated") is False:
                PlayFabManager.__completePlatformIdentityRequest(
                    request_id,
                    "Error",
                    "GooglePlayGamesNotAuthenticated")
                return False

            Mengine.androidMethod(
                PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN,
                "requestServerAuthCode",
                request_id)

            return True

        if provider == "GameCenter":
            if Mengine.iOSGameCenterIsConnect() is False:
                PlayFabManager.__completePlatformIdentityRequest(
                    request_id,
                    "Error",
                    "GameCenterNotAuthenticated")
                return False

            def __game_center_cb(successful, player_id, public_key_url, signature, salt, timestamp):
                PlayFabManager.__onGameCenterIdentityVerification(
                    request_id,
                    successful,
                    player_id,
                    public_key_url,
                    signature,
                    salt,
                    timestamp)

            started = Mengine.iOSGameCenterRequestIdentityVerificationSignature(__game_center_cb)

            if started is False:
                PlayFabManager.__completePlatformIdentityRequest(
                    request_id,
                    "Error",
                    "GameCenterIdentityRequestNotStarted")

            return started

        PlayFabManager.__completePlatformIdentityRequest(
            request_id,
            "Error",
            "UnsupportedPlatformIdentity")

        return False

    @staticmethod
    def __requestPlatformIdentity(success_cb, error_cb, canceled_cb):
        if PlayFabManager.s_platform_identity_request_id is not None:
            error_cb("RequestAlreadyInProgress")
            return False

        provider = None
        authenticated = False
        authenticated_semaphore = None

        if _ANDROID is True:
            if Mengine.isAvailablePlugin(PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN) is False:
                error_cb("GooglePlayGamesUnavailable")
                return False

            provider = "GooglePlayGames"
            authenticated = Mengine.androidBooleanMethod(
                PlayFabManager.GOOGLE_GAME_SOCIAL_PLUGIN,
                "isAuthenticated")
            authenticated_semaphore = "GoogleGameSocialAuthenticated"
        elif _IOS is True:
            if Mengine.isAvailablePlugin(PlayFabManager.IOS_GAME_CENTER_PLUGIN) is False:
                error_cb("GameCenterUnavailable")
                return False

            provider = "GameCenter"
            authenticated = Mengine.iOSGameCenterIsConnect()
            authenticated_semaphore = "GameCenterAuthenticated"
        else:
            error_cb("PlatformIdentityUnavailable")
            return False

        PlayFabManager.s_platform_identity_request_sequence += 1
        request_id = PlayFabManager.s_platform_identity_request_sequence
        PlayFabManager.s_platform_identity_request_id = request_id
        PlayFabManager.s_platform_identity_success_cb = success_cb
        PlayFabManager.s_platform_identity_error_cb = error_cb
        PlayFabManager.s_platform_identity_canceled_cb = canceled_cb

        timeout_delay = DefaultManager.getDefaultInt("PlayFabPlatformIdentityTimeout", 8) * 1000.0
        with TaskManager.createTaskChain(Name=PlayFabManager.PLATFORM_IDENTITY_TIMEOUT_TASK) as timeout:
            timeout.addDelay(timeout_delay)
            timeout.addFunction(PlayFabManager.__onPlatformIdentityTimeout, request_id)

        if authenticated is True:
            return PlayFabManager.__startPlatformIdentityRequest(request_id, provider)

        def __authenticated_cb():
            PlayFabManager.__startPlatformIdentityRequest(request_id, provider)

        Mengine.waitSemaphore(authenticated_semaphore, __authenticated_cb)

        return True

    @staticmethod
    def __onLoginSuccess(identity_provider=None):
        PlayFabManager.initializeIdentityLinking()
        PlayFabManager.__resetIdentityLinkState()

        if identity_provider == "CustomID":
            PlayFabManager.s_custom_id_link_attempted = True
        elif identity_provider in ("GooglePlayGames", "GameCenter"):
            PlayFabManager.s_platform_link_attempted = True

        PlayFabManager.ensureIdentityLinks()

    # = SERVICE =========================================================================================================
    @staticmethod
    def checkErrorHandler(error, handlers, log=False):
        if error not in handlers:
            if log:
                Trace.log("Manager", 0, "[PlayFabManager|checkErrorHandler] no error handler for error '{}'".format(error))
            return False
        elif handlers[error] is None:
            if log:
                Trace.log("Manager", 0, "[PlayFabManager|checkErrorHandler] invalid error handler"
                                        " '{}' for error '{}'".format(handlers[error], error))
            return False
        return True

    @staticmethod
    def checkErrorHandlers(errors, handlers, log=False):
        for error in errors:
            if PlayFabManager.checkErrorHandler(error, handlers, log) is False:
                return False
        return True

    # = BASE ============================================================================================================
    @staticmethod
    def make_api_cb(api_method, success_cb, fail_cb, error_handlers):
        DebugPlayFabLogOnSuccess = DefaultManager.getDefault("DebugPlayFabLogOnSuccess", False)
        DebugPlayFabLogOnFail = DefaultManager.getDefault("DebugPlayFabLogOnFail", False)

        def __cb(response, error):
            if error is not None:
                if DebugPlayFabLogOnFail:
                    PlayFabManager.print_data("[PlayFabManager] '{}' call - ERROR".format(api_method.__name__), error)
                if isinstance(error, PlayFabError) is False:
                    playFabError = PlayFabError(error)
                else:
                    playFabError = error
                error_handler = error_handlers.get(playFabError.Error, fail_cb)

                error_handler(playFabError)

                return

            if response is not None:
                if DebugPlayFabLogOnSuccess:
                    PlayFabManager.print_data("[PlayFabManager] '{}' call - RESPONSE".format(api_method.__name__), response)
                success_cb(response)

                return

            if DebugPlayFabLogOnSuccess:
                PlayFabManager.print_data("[PlayFabManager] '{}' call - EMPTY RESPONSE".format(api_method.__name__), {})

            success_cb({})

        return __cb

    @staticmethod
    def checkPlayFabAPI(api_method, request, success_cb, fail_cb, possible_errors, error_handlers):
        if api_method is None:
            Trace.log("Manager", 0, "[PlayFabManager|callPlayFabAPI] api_method is None")
            return False

        if request is None:
            Trace.log("Manager", 0, "[PlayFabManager|callPlayFabAPI] request is None")
            return False

        if success_cb is None:
            Trace.log("Manager", 0, "[PlayFabManager|callPlayFabAPI] success_cb is None")
            return False

        if fail_cb is None:
            Trace.log("Manager", 0, "[PlayFabManager|callPlayFabAPI] fail_cb is None")
            return False

        if possible_errors is None:
            Trace.log("Manager", 0, "[PlayFabManager|callPlayFabAPI] possible_errors is None")
            return False

        DebugPlayFabLogErrorHandlerCheck = DefaultManager.getDefault("DebugPlayFabLogErrorHandlerCheck", False)

        for error_name in possible_errors:
            PlayFabManager.checkErrorHandler(error_name, error_handlers, log=DebugPlayFabLogErrorHandlerCheck)

        return True

    @staticmethod
    def preparePlayFabAPI(api_method, request, success_cb, fail_cb, possible_errors, error_handlers):
        if PlayFabManager.checkPlayFabAPI(api_method, request, success_cb, fail_cb, possible_errors, error_handlers) is False:
            return

        __api_cb = PlayFabManager.make_api_cb(api_method, success_cb, fail_cb, error_handlers)

        return api_method, request, __api_cb

    @staticmethod
    def callPlayFabAPI(api_prepare_method, *args, **kwargs):
        prepared_api = api_prepare_method(*args, **kwargs)

        if prepared_api is None:
            return False

        api_method, request, __api_cb = prepared_api

        try:
            api_method(request, __api_cb)
        except Exception:
            Trace.log("PlayFab", 0, "PlayFab API request setup failed")

            __api_cb(None, PlayFabError())

            return False

        return True

    @staticmethod
    def scopePlayFabAPI(source, api_prepare_method, *args, **kwargs):
        prepared_api = api_prepare_method(*args, **kwargs)

        if prepared_api is None:
            Trace.log("Manager", 0, "[PlayFabManager|scopePlayFabAPI] invalid prepared API")

            return

        api_method, request, __api_cb = prepared_api

        def __task_cb(isSkip, __complete_cb):
            completed = [False]

            def __complete_once():
                if completed[0] is True:
                    return

                completed[0] = True
                __complete_cb(isSkip)

            def __scope_api_cb(response, error):
                __api_cb(response, error)
                __complete_once()

            try:
                api_method(request, __scope_api_cb)
            except Exception:
                Trace.log("PlayFab", 0, "PlayFab API request setup failed")

                __api_cb(None, PlayFabError())
                __complete_once()

        source.addCallback(__task_cb)

    @staticmethod
    def do_before_cb(cb):
        """
        decorator for adding extra logic before response call api cb
        func must return modified args
        :param cb: api cb (ex. success_cb)
        :return:
        """
        if cb is None:
            Trace.log("Manager", 0, "[PlayFabManager|cb_wrap_with_check] cb is None")
            return None

        def __real_decorator(func):
            def __wrapper(response):
                modified_response = func(response)
                cb(modified_response)
            return __wrapper
        return __real_decorator

    # = API ============================================================================================================
    # RegisterPlayFabUser
    @staticmethod
    def prepareRegisterPlayFabUser(user, password, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            Mengine.changeCurrentAccountSetting("Name", unicode(user))
            Mengine.changeCurrentAccountSetting("Password", unicode(password))
            PlayFabManager.__onLoginSuccess("PlayFab")

            return response

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.RegisterPlayFabUser,
            {
                "Username": user,
                "Password": password,
                "RequireBothUsernameAndEmail": False
            },
            __success_cb, fail_cb,
            [
                "AccountNotFound",
                "InvalidEmailOrPassword",
                "InvalidTitleId",
                "RequestViewConstraintParamsNotAllowed",
            ],
            error_handlers)

    @staticmethod
    def callRegisterPlayFabUser(user, password, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareRegisterPlayFabUser,
            user, password,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeRegisterPlayFabUser(source, user, password, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareRegisterPlayFabUser,
            user, password,
            success_cb, fail_cb, **error_handlers)

    # LoginWithPlayFab
    @staticmethod
    def prepareLoginWithPlayFab(user, password, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            PlayFabManager.__onLoginSuccess("PlayFab")

            return response

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LoginWithPlayFab,
            {
                "Username": user,
                "Password": password,
                "TitleId": "1"
            },
            __success_cb, fail_cb, [
                "AccountNotFound",
                "InvalidTitleId",
                "InvalidUsernameOrPassword",
                "RequestViewConstraintParamsNotAllowed",
            ],
            error_handlers)

    @staticmethod
    def prepareLoginWithCustomID(custom_id, create_account, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            PlayFabManager.__onLoginSuccess("CustomID")

            return response

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LoginWithCustomID,
            {
                "CustomId": str(custom_id),
                "CreateAccount": create_account,
            },
            __success_cb, fail_cb, [
                "AccountNotFound",
                "CustomIdNotLinked",
                "InvalidTitleId",
                "RequestViewConstraintParamsNotAllowed",
            ],
            error_handlers)

    @staticmethod
    def prepareLinkCustomID(custom_id, force_link, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LinkCustomID,
            {
                "CustomId": str(custom_id),
                "ForceLink": force_link,
            },
            success_cb, fail_cb, [
                "AccountLinkedToABannedPlayer",
                "LinkedIdentifierAlreadyClaimed",
            ],
            error_handlers)

    @staticmethod
    def prepareLoginWithGooglePlayGamesServices(server_auth_code, create_account, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            PlayFabManager.__onLoginSuccess("GooglePlayGames")

            return response

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LoginWithGooglePlayGamesServices,
            {
                "ServerAuthCode": server_auth_code,
                "CreateAccount": create_account,
            },
            __success_cb, fail_cb, [
                "AccountNotFound",
                "GoogleOAuthError",
                "GoogleOAuthNotConfiguredForTitle",
                "InvalidGooglePlayGamesServerAuthCode",
                "InvalidGoogleToken",
                "InvalidTitleId",
            ],
            error_handlers)

    @staticmethod
    def prepareLinkGooglePlayGamesServicesAccount(server_auth_code, force_link, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LinkGooglePlayGamesServicesAccount,
            {
                "ServerAuthCode": server_auth_code,
                "ForceLink": force_link,
            },
            success_cb, fail_cb, [
                "AccountAlreadyLinked",
                "AccountLinkedToABannedPlayer",
                "GoogleOAuthError",
                "GoogleOAuthNotConfiguredForTitle",
                "InvalidGooglePlayGamesServerAuthCode",
                "InvalidGoogleToken",
                "LinkedAccountAlreadyClaimed",
            ],
            error_handlers)

    @staticmethod
    def __makeGameCenterRequest(identity_verification, create_account=None, force_link=None):
        request = {
            "GameCenterId": identity_verification["GameCenterId"],
            "PublicKeyUrl": identity_verification["PublicKeyUrl"],
            "Salt": identity_verification["Salt"],
            "Signature": identity_verification["Signature"],
            "Timestamp": identity_verification["Timestamp"],
        }

        if create_account is not None:
            request["PlayerId"] = request.pop("GameCenterId")
            request["CreateAccount"] = create_account

        if force_link is not None:
            request["ForceLink"] = force_link

        return request

    @staticmethod
    def prepareLoginWithGameCenter(identity_verification, create_account, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            PlayFabManager.__onLoginSuccess("GameCenter")

            return response

        request = PlayFabManager.__makeGameCenterRequest(identity_verification, create_account=create_account)

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LoginWithGameCenter,
            request,
            __success_cb, fail_cb, [
                "AccountNotFound",
                "GameCenterAuthenticationFailed",
                "InvalidGameCenterAuthRequest",
                "InvalidTitleId",
            ],
            error_handlers)

    @staticmethod
    def prepareLinkGameCenterAccount(identity_verification, force_link, success_cb, fail_cb, **error_handlers):
        request = PlayFabManager.__makeGameCenterRequest(identity_verification, force_link=force_link)

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LinkGameCenterAccount,
            request,
            success_cb, fail_cb, [
                "AccountAlreadyLinked",
                "AccountLinkedToABannedPlayer",
                "GameCenterAuthenticationFailed",
                "InvalidGameCenterAuthRequest",
                "LinkedAccountAlreadyClaimed",
            ],
            error_handlers)

    @staticmethod
    def prepareLoginWithAndroidDeviceID(device_id, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            PlayFabManager.__onLoginSuccess("AndroidDeviceID")

            return response

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LoginWithAndroidDeviceID,
            {
                "AndroidDeviceId": str(device_id),
                "CreateAccount": False
            },
            __success_cb, fail_cb, [
                "EncryptionKeyMissing",
                "EvaluationModePlayerCountExceeded",
                "InvalidSignature",
                "InvalidSignatureTime",
                "PlayerSecretAlreadyConfigured",
                "PlayerSecretNotConfigured",
                "RequestViewConstraintParamsNotAllowed",
            ],
            error_handlers)

    @staticmethod
    def prepareLinkAndroidDeviceID(device_id, force_link, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LinkAndroidDeviceID,
            {
                "AndroidDeviceId": str(device_id),
                "ForceLink": force_link,
            },
            success_cb, fail_cb, [
                "LinkedDeviceAlreadyClaimed",
            ],
            error_handlers)

    @staticmethod
    def prepareUnLinkAndroidDeviceID(device_id, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.UnlinkAndroidDeviceID,
            {
                "AndroidDeviceId": str(device_id),
            },
            success_cb, fail_cb, [
                "AccountNotLinked",
                "DeviceNotLinked"
            ],
            error_handlers)

    @staticmethod
    def callLoginWithPlayFab(user, password, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareLoginWithPlayFab,
            user, password,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def callLoginWithCustomID(custom_id, create_account, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareLoginWithCustomID,
            custom_id, create_account,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def callLinkCustomID(custom_id, force_link, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareLinkCustomID,
            custom_id, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def callLoginWithGooglePlayGamesServices(server_auth_code, create_account, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareLoginWithGooglePlayGamesServices,
            server_auth_code, create_account,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def callLinkGooglePlayGamesServicesAccount(server_auth_code, force_link, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareLinkGooglePlayGamesServicesAccount,
            server_auth_code, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def callLoginWithGameCenter(identity_verification, create_account, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareLoginWithGameCenter,
            identity_verification, create_account,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def callLinkGameCenterAccount(identity_verification, force_link, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareLinkGameCenterAccount,
            identity_verification, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginWithPlayFab(source, user, password, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLoginWithPlayFab,
            user, password,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginWithCustomID(source, custom_id, create_account, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLoginWithCustomID,
            custom_id, create_account,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLinkCustomID(source, custom_id, force_link, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLinkCustomID,
            custom_id, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginWithGooglePlayGamesServices(source, server_auth_code, create_account, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLoginWithGooglePlayGamesServices,
            server_auth_code, create_account,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLinkGooglePlayGamesServicesAccount(source, server_auth_code, force_link, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLinkGooglePlayGamesServicesAccount,
            server_auth_code, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginWithGameCenter(source, identity_verification, create_account, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLoginWithGameCenter,
            identity_verification, create_account,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLinkGameCenterAccount(source, identity_verification, force_link, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLinkGameCenterAccount,
            identity_verification, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginWithPlatformAccount(source, success_cb, fallback_cb):
        def __task_cb(isSkip, __complete_cb):
            completed = [False]

            def __complete_once(cb, value):
                if completed[0] is True:
                    return

                completed[0] = True
                cb(value)
                __complete_cb(isSkip)

            def __login_success(response):
                __complete_once(success_cb, response)

            def __login_fallback(reason):
                __complete_once(fallback_cb, reason)

            def __identity_success(identity):
                provider = identity.get("Provider")
                credential = identity.get("Credential")

                if provider == "GooglePlayGames":
                    error_handlers = dict((error, __login_fallback) for error in [
                        "AccountNotFound",
                        "GoogleOAuthError",
                        "GoogleOAuthNotConfiguredForTitle",
                        "InvalidGooglePlayGamesServerAuthCode",
                        "InvalidGoogleToken",
                        "InvalidTitleId",
                    ])
                    started = PlayFabManager.callLoginWithGooglePlayGamesServices(
                        credential,
                        False,
                        __login_success,
                        __login_fallback,
                        **error_handlers)
                elif provider == "GameCenter":
                    error_handlers = dict((error, __login_fallback) for error in [
                        "AccountNotFound",
                        "GameCenterAuthenticationFailed",
                        "InvalidGameCenterAuthRequest",
                        "InvalidTitleId",
                    ])
                    started = PlayFabManager.callLoginWithGameCenter(
                        credential,
                        False,
                        __login_success,
                        __login_fallback,
                        **error_handlers)
                else:
                    __login_fallback("UnsupportedPlatformIdentity")
                    return

                if started is False:
                    __login_fallback("PlatformLoginNotStarted")

            if isSkip is True:
                __complete_cb(isSkip)
                return

            PlayFabManager.__requestPlatformIdentity(
                __identity_success,
                __login_fallback,
                __login_fallback)

        source.addCallback(__task_cb)

    @staticmethod
    def getOrCreateCustomID():
        custom_id = Mengine.getCurrentAccountSetting("PlayFabCustomId")

        if custom_id:
            return str(custom_id)

        custom_id = Mengine.generateUniqueIdentity(64)

        Mengine.changeCurrentAccountSetting("PlayFabCustomId", unicode(custom_id))
        Mengine.saveAccounts()

        return str(custom_id)

    @staticmethod
    def ensureIdentityLinks():
        if PlayFabSettings._internalSettings.ClientSessionTicket is None:
            return False

        if PlayFabManager.s_custom_id_link_attempted is False:
            return PlayFabManager.__tryLinkCustomID()

        return PlayFabManager.__tryLinkPlatformAccount()

    @staticmethod
    def __tryLinkCustomID():
        if PlayFabManager.s_custom_id_link_in_progress is True:
            return False

        custom_id = PlayFabManager.getOrCreateCustomID()

        PlayFabManager.s_custom_id_link_in_progress = True

        def __success_cb(response):
            PlayFabManager.s_custom_id_link_in_progress = False
            PlayFabManager.s_custom_id_link_attempted = True

            Trace.msg_dev("[PlayFab] CustomID link success")

            PlayFabManager.__tryLinkPlatformAccount()

        def __fail_cb(error):
            PlayFabManager.s_custom_id_link_in_progress = False
            PlayFabManager.s_custom_id_link_attempted = True

            Trace.msg_warn("[PlayFab] CustomID link skipped: {}".format(error.Error))

            PlayFabManager.__tryLinkPlatformAccount()

        return PlayFabManager.callLinkCustomID(
            custom_id,
            False,
            __success_cb,
            __fail_cb,
            AccountLinkedToABannedPlayer=__fail_cb,
            LinkedIdentifierAlreadyClaimed=__fail_cb)

    @staticmethod
    def __tryLinkPlatformAccount():
        if PlayFabManager.s_platform_link_in_progress is True or PlayFabManager.s_platform_link_attempted is True:
            return False

        if PlayFabManager.isPlatformIdentitySupported() is False:
            PlayFabManager.s_platform_link_attempted = True
            Trace.msg_dev("[PlayFab] Platform identity link is not supported on this build")
            return False

        PlayFabManager.s_platform_link_in_progress = True

        def __identity_success(identity):
            PlayFabManager.__linkPlatformIdentity(identity)

        def __identity_failed(reason):
            PlayFabManager.s_platform_link_in_progress = False
            PlayFabManager.s_platform_link_attempted = True

            Trace.msg_warn("[PlayFab] Platform identity link skipped: {}".format(reason))

        return PlayFabManager.__requestPlatformIdentity(
            __identity_success,
            __identity_failed,
            __identity_failed)

    @staticmethod
    def __linkPlatformIdentity(identity):
        provider = identity.get("Provider")
        credential = identity.get("Credential")

        def __success_cb(response):
            PlayFabManager.s_platform_link_in_progress = False
            PlayFabManager.s_platform_link_attempted = True

            Trace.msg_dev("[PlayFab] {} link success".format(provider))

        def __already_linked_cb(error):
            PlayFabManager.s_platform_link_in_progress = False
            PlayFabManager.s_platform_link_attempted = True

            Trace.msg_dev("[PlayFab] {} account is already linked".format(provider))

        def __fail_cb(error):
            PlayFabManager.s_platform_link_in_progress = False
            PlayFabManager.s_platform_link_attempted = True

            Trace.msg_warn("[PlayFab] {} link failed: {}".format(provider, error.Error))

        if provider == "GooglePlayGames":
            return PlayFabManager.callLinkGooglePlayGamesServicesAccount(
                credential,
                False,
                __success_cb,
                __fail_cb,
                AccountAlreadyLinked=__already_linked_cb,
                AccountLinkedToABannedPlayer=__fail_cb,
                GoogleOAuthError=__fail_cb,
                GoogleOAuthNotConfiguredForTitle=__fail_cb,
                InvalidGooglePlayGamesServerAuthCode=__fail_cb,
                InvalidGoogleToken=__fail_cb,
                LinkedAccountAlreadyClaimed=__fail_cb)

        if provider == "GameCenter":
            return PlayFabManager.callLinkGameCenterAccount(
                credential,
                False,
                __success_cb,
                __fail_cb,
                AccountAlreadyLinked=__already_linked_cb,
                AccountLinkedToABannedPlayer=__fail_cb,
                GameCenterAuthenticationFailed=__fail_cb,
                InvalidGameCenterAuthRequest=__fail_cb,
                LinkedAccountAlreadyClaimed=__fail_cb)

        PlayFabManager.s_platform_link_in_progress = False
        PlayFabManager.s_platform_link_attempted = True

        Trace.msg_warn("[PlayFab] Unsupported platform identity provider")

        return False

    @staticmethod
    def __onGooglePlayGamesServerAuthCodeSuccess(request_id, server_auth_code):
        identity = {
            "Provider": "GooglePlayGames",
            "Credential": server_auth_code,
        }

        PlayFabManager.__completePlatformIdentityRequest(request_id, "Success", identity)

    @staticmethod
    def __onGooglePlayGamesServerAuthCodeError(request_id, error):
        PlayFabManager.__completePlatformIdentityRequest(
            request_id,
            "Error",
            "GooglePlayGamesServerAuthCodeError")

    @staticmethod
    def __onGooglePlayGamesServerAuthCodeCanceled(request_id):
        PlayFabManager.__completePlatformIdentityRequest(
            request_id,
            "Canceled",
            "GooglePlayGamesServerAuthCodeCanceled")

    @staticmethod
    def __onGameCenterIdentityVerification(request_id, successful, player_id, public_key_url, signature, salt, timestamp):
        if successful is False:
            PlayFabManager.__completePlatformIdentityRequest(
                request_id,
                "Error",
                "GameCenterIdentityVerificationError")

            return

        identity_verification = {
            "GameCenterId": player_id,
            "PublicKeyUrl": public_key_url,
            "Signature": signature,
            "Salt": salt,
            "Timestamp": timestamp,
        }

        identity = {
            "Provider": "GameCenter",
            "Credential": identity_verification,
        }

        PlayFabManager.__completePlatformIdentityRequest(request_id, "Success", identity)

    @staticmethod
    def scopeLoginWithAndroidDeviceID(source, device_id, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLoginWithAndroidDeviceID,
            device_id,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLinkAndroidDeviceID(source, device_id, force_link, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLinkAndroidDeviceID,
            device_id, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeUnLinkAndroidDeviceID(source, device_id, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareUnLinkAndroidDeviceID,
            device_id,
            success_cb, fail_cb, **error_handlers)

    # UpdateUserTitleDisplayName

    @staticmethod
    def getDefaultDisplayName():
        if DefaultManager.hasDefault("DefaultUserDisplayNameTextID") is False:
            return

        display_name_text_id = DefaultManager.getDefault("DefaultUserDisplayNameTextID")
        if Mengine.existText(display_name_text_id) is False:
            Trace.log("PlayFab", 0, "Not found default display name text id: {}".format(display_name_text_id))

        display_name = Mengine.getTextFromId(display_name_text_id)
        return display_name

    @staticmethod
    def setDefaultDisplayName():
        display_name = PlayFabManager.getDefaultDisplayName()
        if display_name is None:
            return
        Mengine.changeCurrentAccountSetting("DisplayName", unicode(display_name))

    @staticmethod
    def prepareUpdateUserTitleDisplayName(new_name, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("DisplayName", {})
            return Data

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.UpdateUserTitleDisplayName,
            {
                "DisplayName": new_name
            },
            __success_cb, fail_cb, [
                "InvalidPartnerResponse",
                "NameNotAvailable",
                "ProfaneDisplayName",
                "UsernameNotAvailable",
            ],
            error_handlers)

    @staticmethod
    def callUpdateUserTitleDisplayName(new_name, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareUpdateUserTitleDisplayName,
            new_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeUpdateUserTitleDisplayName(source, new_name, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareUpdateUserTitleDisplayName,
            new_name,
            success_cb, fail_cb, **error_handlers)

    # GetUserReadOnlyData
    @staticmethod
    def prepareGetUserReadOnlyData(list_of_keys, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            data = response.get("Data", {})
            return data

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.GetUserReadOnlyData,
            {
                "Keys": list_of_keys
            },
            __success_cb, fail_cb,
            [
                # no possible error codes in playfab documentation
            ],
            error_handlers)

    @staticmethod
    def callGetUserReadOnlyData(list_of_keys, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareGetUserReadOnlyData,
            list_of_keys,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetUserReadOnlyData(source, list_of_keys, success_cb, fail_cb, **error_handlers):
        source.addScope(PlayFabManager.scopePlayFabAPI,
                        PlayFabManager.prepareGetUserReadOnlyData,
                        list_of_keys,
                        success_cb, fail_cb, **error_handlers)

    # GetTitleData
    @staticmethod
    def prepareGetTitleData(list_of_keys, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("Data", {})
            return Data

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.GetTitleData,
            {
                "Keys": list_of_keys
            },
            __success_cb, fail_cb,
            [
                # no possible error codes in playfab documentation
            ],
            error_handlers)

    @staticmethod
    def callGetTitleData(list_of_keys, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareGetTitleData,
            list_of_keys,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetTitleData(source, list_of_keys, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareGetTitleData,
            list_of_keys,
            success_cb, fail_cb, **error_handlers)

    # GetLeaderboard
    @staticmethod
    def prepareGetLeaderboard(statistic_name, max_result_count, profile_constraints,
                              success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("Leaderboard", {})
            return Data

        if not profile_constraints:
            profile_constraints = {}

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.GetLeaderboard,
            {
                "StartPosition": 0,
                "StatisticName": statistic_name,
                "MaxResultsCount": max_result_count,
                "ProfileConstraints": profile_constraints
            },
            __success_cb, fail_cb,
            [
                "LeaderboardVersionNotAvailable"
            ],
            error_handlers)

    @staticmethod
    def callGetLeaderboard(statistic_name, max_result_count, profile_constraints,
                           success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareGetLeaderboard,
            statistic_name, max_result_count, profile_constraints,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetLeaderboard(source, statistic_name, max_result_count, profile_constraints,
                            success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareGetLeaderboard,
            statistic_name, max_result_count, profile_constraints,
            success_cb, fail_cb, **error_handlers)

    # GetLeaderboardAroundPlayer
    @staticmethod
    def prepareGetLeaderboardAroundPlayer(statistic_name, max_result_count, profile_constraints,
                                          success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("Leaderboard", {})
            return Data

        if not profile_constraints:
            profile_constraints = {}

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.GetLeaderboardAroundPlayer,
            {
                "StatisticName": statistic_name,
                "MaxResultsCount": max_result_count,
                "ProfileConstraints": profile_constraints
            },
            __success_cb, fail_cb,
            [
                "AccountNotFound",
                "LeaderboardVersionNotAvailable"
            ],
            error_handlers)

    @staticmethod
    def callGetLeaderboardAroundPlayer(statistic_name, max_result_count, profile_constraints,
                                       success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareGetLeaderboardAroundPlayer,
            statistic_name, max_result_count, profile_constraints,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetLeaderboardAroundPlayer(source, statistic_name, max_result_count, profile_constraints,
                                        success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareGetLeaderboardAroundPlayer,
            statistic_name, max_result_count, profile_constraints,
            success_cb, fail_cb, **error_handlers)

    # GetAccountInfo
    @staticmethod
    def prepareGetAccountInfo(success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("AccountInfo", {})
            return Data

        playfab_id = Mengine.getCurrentAccountSetting("PlayFabId")

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.GetAccountInfo,
            {
                "PlayFabId": playfab_id
            },
            __success_cb, fail_cb,
            [
                "AccountNotFound"
            ],
            error_handlers)

    @staticmethod
    def callGetAccountInfo(success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareGetAccountInfo,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetAccountInfo(source, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareGetAccountInfo,
            success_cb, fail_cb, **error_handlers)

    # GetPlayerStatistics
    @staticmethod
    def prepareGetPlayerStatistics(statistic_names, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("Statistics", {})
            return Data

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.GetPlayerStatistics,
            {
                "StatisticNames": statistic_names
            },
            __success_cb, fail_cb,
            [
                # no possible error codes in playfab documentation
            ],
            error_handlers)

    @staticmethod
    def callGetPlayerStatistics(statistic_names, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareGetPlayerStatistics,
            statistic_names,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetPlayerStatistics(source, statistic_names, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareGetPlayerStatistics,
            statistic_names,
            success_cb, fail_cb, **error_handlers)

    # UpdatePlayerStatistics
    @staticmethod
    def prepareUpdatePlayerStatistics(statistics, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.UpdatePlayerStatistics,
            {
                "Statistics": statistics
            },
            success_cb, fail_cb,
            [
                "AccountNotFound",
                "APINotEnabledForGameClientAccess",
                "DuplicateStatisticName",
                "StatisticCountLimitExceeded",
                "StatisticNameConflict",
                "StatisticNotFound",
                "StatisticValueAggregationOverflow",
                "StatisticVersionClosedForWrites",
                "StatisticVersionInvalid",
            ],
            error_handlers)

    @staticmethod
    def callUpdatePlayerStatistics(statistics, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareUpdatePlayerStatistics,
            statistics,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeUpdatePlayerStatistics(source, statistics, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareUpdatePlayerStatistics,
            statistics,
            success_cb, fail_cb, **error_handlers)

    # UpdateAvatarUrl
    @staticmethod
    def prepareUpdateAvatarUrl(image_url, success_cb, fail_cb, **error_handlers):
        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.UpdateAvatarUrl,
            {
                "ImageUrl": image_url
            },
            success_cb, fail_cb,
            [
                # no possible error codes in pl__on_get_profile_picture_linkayfab documentation
            ],
            error_handlers)

    @staticmethod
    def callUpdateAvatarUrl(image_url, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareUpdateAvatarUrl,
            image_url,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeUpdateAvatarUrl(source, image_url, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareUpdateAvatarUrl,
            image_url,
            success_cb, fail_cb, **error_handlers)

    # ExecuteCloudScript
    @staticmethod
    def prepareExecuteCloudScript(function_name, params, success_cb, fail_cb, **error_handlers):
        # print "[PlayFabManager|ExecuteCloudScript] CALL '{}' with params={}".format(function_name, params)

        revision = DefaultManager.getDefault("DefaultRevisionSelection", "Live")

        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            # print " ^-- [PlayFabManager|ExecuteCloudScript] SUCCESS '{}' --^\n".format(function_name)

            function_result = response.get("FunctionResult")
            return function_result

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.ExecuteCloudScript,
            {
                "FunctionName": function_name,
                "FunctionParameter": params,
                "RevisionSelection": revision,
            },
            __success_cb, fail_cb,
            [
                "CloudScriptAPIRequestCountExceeded",
                "CloudScriptAPIRequestError",
                "CloudScriptFunctionArgumentSizeExceeded",
                "CloudScriptHTTPRequestError",
                "CloudScriptNotFound",
                "JavascriptException",
            ],
            error_handlers)

    @staticmethod
    def callExecuteCloudScript(function_name, params, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareExecuteCloudScript,
            function_name, params,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeExecuteCloudScript(source, function_name, params, success_cb, fail_cb, **error_handlers):
        source.addScope(PlayFabManager.scopeAddToTimeStampsQueue, function_name)
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareExecuteCloudScript,
            function_name, params,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeAddToTimeStampsQueue(source, function_name=None):
        current_timestamp = Mengine.getTimeMs() / 1000

        if len(PlayFabManager.timestamps_queue) == 0:
            source.addFunction(PlayFabManager.timestamps_queue.append, current_timestamp)
            return

        if current_timestamp - PlayFabManager.timestamps_queue[-1] <= 2:
            if _DEVELOPMENT is True:
                Trace.log("Manager", 0, "Warning!!! Less than 2 seconds passed between requests (call {})".format(function_name))
            else:
                Trace.msg_err("PlayFabManager [W] Less than 2 seconds passed between requests (call {})".format(function_name))

        if len(PlayFabManager.timestamps_queue) >= 10:
            old_time_stamp = PlayFabManager.timestamps_queue.pop(0)

            if current_timestamp - old_time_stamp <= 10:
                Trace.log("Manager", 0, 'Warning!!! limit "Player data value updates per 15 seconds" has been exceeded')

        source.addFunction(PlayFabManager.timestamps_queue.append, current_timestamp)
