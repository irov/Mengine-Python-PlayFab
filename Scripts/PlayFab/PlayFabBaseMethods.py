from Foundation.DefaultManager import DefaultManager
from PlayFab.PlayFabErrors import PlayFabError
import PlayFab.PlayFabSettings as PlayFabSettings


class PlayFabBaseMethods(object):
    # = DEBUG ==========================================================================================================
    @staticmethod
    def print_data(msg, data):
        DebugPlayFabResponseDataPrint = DefaultManager.getDefaultBool("DebugPlayFabResponseDataPrint", False)

        if (isinstance(data, PlayFabError) is False and
                DefaultManager.getDefaultBool("DebugDataPrettyPrint", False) is True):
            data = Mengine.encodeJSON(data, indent=2)

        LINE_CHAR_COUNT = 79
        Trace.msg("\n" + " {} ".format(msg).center(LINE_CHAR_COUNT, '#'))

        if DebugPlayFabResponseDataPrint is True:
            Trace.msg(data)
        else:
            Trace.msg("! PlayFab response data print is disabled.")
            Trace.msg("! For enable change default param 'DebugPlayFabResponseDataPrint' to True")

        Trace.msg("#" * LINE_CHAR_COUNT + "\n")

    # = SERVICE ========================================================================================================
    @staticmethod
    def checkErrorHandler(error, handlers, log=False):
        if error not in handlers:
            if log:
                Trace.msg_dev(
                    "[PlayFab] No dedicated error handler for '{}'; using default fail callback".format(error))
            return False

        if handlers[error] is None:
            if log:
                Trace.msg_warn("[PlayFab] Invalid None handler for error '{}'".format(error))
            return False

        return True

    # = BASE ===========================================================================================================
    @staticmethod
    def make_api_cb(api_method, success_cb, fail_cb, error_handlers):
        DebugPlayFabLogOnSuccess = DefaultManager.getDefault("DebugPlayFabLogOnSuccess", False)
        DebugPlayFabLogOnFail = DefaultManager.getDefault("DebugPlayFabLogOnFail", False)

        def __cb(response, error):
            if error is not None:
                if DebugPlayFabLogOnFail:
                    PlayFabBaseMethods.print_data("[PlayFab] '{}' call - ERROR".format(api_method.__name__), error)
                if isinstance(error, PlayFabError) is False:
                    playFabError = PlayFabError(error)
                else:
                    playFabError = error
                error_handler = error_handlers.get(playFabError.Error) or fail_cb

                error_handler(playFabError)

                return

            if response is not None:
                if DebugPlayFabLogOnSuccess:
                    PlayFabBaseMethods.print_data("[PlayFab] '{}' call - RESPONSE".format(api_method.__name__), response)
                success_cb(response)

                return

            if DebugPlayFabLogOnSuccess:
                PlayFabBaseMethods.print_data("[PlayFab] '{}' call - EMPTY RESPONSE".format(api_method.__name__), {})

            success_cb({})

        return __cb

    @staticmethod
    def checkPlayFabAPI(api_method, request, success_cb, fail_cb, possible_errors, error_handlers):
        if api_method is None:
            Trace.log("Manager", 0, "[PlayFab|callPlayFabAPI] api_method is None")
            return False

        if request is None:
            Trace.log("Manager", 0, "[PlayFab|callPlayFabAPI] request is None")
            return False

        if success_cb is None:
            Trace.log("Manager", 0, "[PlayFab|callPlayFabAPI] success_cb is None")
            return False

        if fail_cb is None:
            Trace.log("Manager", 0, "[PlayFab|callPlayFabAPI] fail_cb is None")
            return False

        if possible_errors is None:
            Trace.log("Manager", 0, "[PlayFab|callPlayFabAPI] possible_errors is None")
            return False

        DebugPlayFabLogErrorHandlerCheck = DefaultManager.getDefault("DebugPlayFabLogErrorHandlerCheck", False)

        for error_name in possible_errors:
            PlayFabBaseMethods.checkErrorHandler(error_name, error_handlers, log=DebugPlayFabLogErrorHandlerCheck)

        return True

    @staticmethod
    def preparePlayFabAPI(api_method, request, success_cb, fail_cb, possible_errors, error_handlers):
        if PlayFabBaseMethods.checkPlayFabAPI(api_method, request, success_cb, fail_cb, possible_errors, error_handlers) is False:
            return

        __api_cb = PlayFabBaseMethods.make_api_cb(api_method, success_cb, fail_cb, error_handlers)

        return api_method, request, __api_cb

    @staticmethod
    def callPlayFabAPI(api_prepare_method, *args, **kwargs):
        try:
            prepared_api = api_prepare_method(*args, **kwargs)
        except Exception as e:
            PlayFabSettings.GlobalExceptionLogger(e)

            return False

        if prepared_api is None:
            return False

        api_method, request, __api_cb = prepared_api
        callback_called = [False]

        def __callback(response, error):
            if callback_called[0] is True:
                return

            callback_called[0] = True

            try:
                __api_cb(response, error)
            except Exception as e:
                PlayFabSettings.GlobalExceptionLogger(e)

        try:
            api_method(request, __callback)
        except Exception as e:
            PlayFabSettings.GlobalExceptionLogger(e)

            if callback_called[0] is False:
                __callback(None, PlayFabError())

            return False

        return True

    @staticmethod
    def scopePlayFabAPI(source, api_prepare_method, *args, **kwargs):
        try:
            prepared_api = api_prepare_method(*args, **kwargs)
        except Exception as e:
            PlayFabSettings.GlobalExceptionLogger(e)

            return

        if prepared_api is None:
            Trace.log("Manager", 0, "[PlayFab|scopePlayFabAPI] invalid prepared API")

            return

        api_method, request, __api_cb = prepared_api

        def __task_cb(isSkip, __complete_cb):
            if isSkip is True:
                __complete_cb(isSkip)
                return

            completed = [False]

            def __callback(response, error):
                if completed[0] is True:
                    return

                completed[0] = True
                try:
                    __api_cb(response, error)
                except Exception as e:
                    PlayFabSettings.GlobalExceptionLogger(e)
                finally:
                    __complete_cb(isSkip)

            try:
                api_method(request, __callback)
            except Exception as e:
                PlayFabSettings.GlobalExceptionLogger(e)

                if completed[0] is False:
                    __callback(None, PlayFabError())

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
            Trace.log("Manager", 0, "[PlayFab|cb_wrap_with_check] cb is None")
            return None

        def __real_decorator(func):
            def __wrapper(response):
                cb(func(response))
            return __wrapper
        return __real_decorator
