from Foundation.DefaultManager import DefaultManager
from Foundation.Manager import Manager
from PlayFab.PlayFabErrors import PlayFabError
import PlayFab.PlayFabClientAPI as PlayFabClientAPI


class PlayFabManager(Manager):
    timestamps_queue = []
    s_debug_pretty_print = False

    # = DEBUG ===========================================================================================================
    @staticmethod
    def print_data(msg, data):
        DebugPlayFabResponseDataPrint = DefaultManager.getDefaultBool("DebugPlayFabResponseDataPrint", False)

        if isinstance(data, PlayFabError) is False and PlayFabManager.s_debug_pretty_print is True:
            from json import dumps
            data = dumps(data, indent=2)

        LINE_CHAR_COUNT = 79
        print()
        print(" {} ".format(msg).center(LINE_CHAR_COUNT, '#'))

        if DebugPlayFabResponseDataPrint is True:
            print(data)
        else:
            print("! PlayFab response data print is disabled.")
            print("! For enable change default param 'DebugPlayFabResponseDataPrint' to True")

        print("#" * LINE_CHAR_COUNT)
        print()

    # = INIT ============================================================================================================
    @staticmethod
    def _onInitialize(*args):
        PlayFabManager.s_debug_pretty_print = DefaultManager.getDefaultBool("DebugDataPrettyPrint", False)

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

            if response is not None:
                if DebugPlayFabLogOnSuccess:
                    PlayFabManager.print_data("[PlayFabManager] '{}' call - RESPONSE".format(api_method.__name__), response)
                success_cb(response)

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
        api_method, request, __api_cb = api_prepare_method(*args, **kwargs)

        api_method(request, __api_cb)

    @staticmethod
    def scopePlayFabAPI(source, api_prepare_method, *args, **kwargs):
        api_method, request, __api_cb = api_prepare_method(*args, **kwargs)

        def __task_cb(isSkip, __complete_cb):
            def __scope_api_cb(response, error):
                __api_cb(response, error)
                __complete_cb(isSkip)

            api_method(request, __scope_api_cb)

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
            # Mengine.changeCurrentAccountSetting("DisplayName", unicode(user))
            Mengine.changeCurrentAccountSetting("Password", unicode(password))
            return response

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.RegisterPlayFabUser,
            {
                "Username": user,
                # "DisplayName": user,
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
        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.LoginWithPlayFab,
            {
                "Username": user,
                "Password": password,
                "TitleId": "1"
            },
            success_cb, fail_cb, [
                "AccountNotFound",
                "InvalidTitleId",
                "InvalidUsernameOrPassword",
                "RequestViewConstraintParamsNotAllowed",
            ],
            error_handlers)

    @staticmethod
    def callLoginWithPlayFab(user, password, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareLoginWithPlayFab,
            user, password,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginWithPlayFab(source, user, password, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareLoginWithPlayFab,
            user, password,
            success_cb, fail_cb, **error_handlers)

    # UpdateUserTitleDisplayName
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
    def prepareGetLeaderboard(statistic_name, max_result_count, success_cb, fail_cb, **error_handlers):
        @PlayFabManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("Leaderboard", {})
            return Data

        return PlayFabManager.preparePlayFabAPI(
            PlayFabClientAPI.GetLeaderboard,
            {
                "StartPosition": 0,
                "StatisticName": statistic_name,
                "MaxResultsCount": max_result_count
            },
            __success_cb, fail_cb,
            [
                "LeaderboardVersionNotAvailable"
            ],
            error_handlers)

    @staticmethod
    def callGetLeaderboard(statistic_name, max_result_count, success_cb, fail_cb, **error_handlers):
        PlayFabManager.callPlayFabAPI(
            PlayFabManager.prepareGetLeaderboard,
            statistic_name, max_result_count,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetLeaderboard(source, statistic_name, max_result_count, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareGetLeaderboard,
            statistic_name, max_result_count,
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
        source.addScope(PlayFabManager.scopeAddToTimeStampsQueue)
        source.addScope(
            PlayFabManager.scopePlayFabAPI,
            PlayFabManager.prepareExecuteCloudScript,
            function_name, params,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeAddToTimeStampsQueue(source):
        current_timestamp = Mengine.getTimeMs() / 1000

        if len(PlayFabManager.timestamps_queue) == 0:
            source.addFunction(PlayFabManager.timestamps_queue.append, current_timestamp)
            return

        if current_timestamp - PlayFabManager.timestamps_queue[-1] <= 2:
            Trace.log("Manager", 0, "Warning!!! Less than 2 seconds passed between requests")

            pass

        if len(PlayFabManager.timestamps_queue) >= 10:
            old_time_stamp = PlayFabManager.timestamps_queue.pop(0)

            if current_timestamp - old_time_stamp <= 10:
                Trace.log("Manager", 0, 'Warning!!! limit"Player data value updates per 15 seconds" has been exceeded')

                source.addDelay(2)
        source.addFunction(PlayFabManager.timestamps_queue.append, current_timestamp)
