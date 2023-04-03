from Foundation.DefaultManager import DefaultManager
from PlayFab.PlayFabErrors import PlayFabError


class PlayFabBaseMethods(object):
    s_debug_pretty_print = None

    # = DEBUG ==========================================================================================================
    @staticmethod
    def print_data(msg, data):
        DebugPlayFabResponseDataPrint = DefaultManager.getDefaultBool("DebugPlayFabResponseDataPrint", False)

        if isinstance(data, PlayFabError) is False and PlayFabBaseMethods.s_debug_pretty_print is True:
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

    # = SERVICE ========================================================================================================
    @staticmethod
    def checkErrorHandler(error, handlers, log=False):
        if error not in handlers:
            if log:
                Trace.log("Manager", 0, "[PlayFabBaseMethods|checkErrorHandler] no error handler for error '{}'".format(error))
            return False
        elif handlers[error] is None:
            if log:
                Trace.log("Manager", 0, "[PlayFabBaseMethods|checkErrorHandler] invalid error handler '{}' for error '{}'".format(handlers[error], error))
            return False
        return True

    @staticmethod
    def checkErrorHandlers(errors, handlers, log=False):
        for error in errors:
            if PlayFabBaseMethods.checkErrorHandler(error, handlers, log) is False:
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
                    PlayFabBaseMethods.print_data("[PlayFabBaseMethods] '{}' call - ERROR".format(api_method.__name__), error)
                if isinstance(error, PlayFabError) is False:
                    playFabError = PlayFabError(error)
                else:
                    playFabError = error
                error_handler = error_handlers.get(playFabError.Error, fail_cb)

                error_handler(playFabError)

            if response is not None:
                if DebugPlayFabLogOnSuccess:
                    PlayFabBaseMethods.print_data("[PlayFabBaseMethods] '{}' call - RESPONSE".format(api_method.__name__), response)
                success_cb(response)

            if error is None and response is None:
                response = {}
                if DebugPlayFabLogOnSuccess:
                    PlayFabBaseMethods.print_data("[PlayFabBaseMethods] '{}' call - RESPONSE".format(api_method.__name__), response)
                success_cb(response)

        return __cb

    @staticmethod
    def checkPlayFabAPI(api_method, request, success_cb, fail_cb, possible_errors, error_handlers):
        if api_method is None:
            Trace.log("Manager", 0, "[PlayFabBaseMethods|callPlayFabAPI] api_method is None")
            return False

        if request is None:
            Trace.log("Manager", 0, "[PlayFabBaseMethods|callPlayFabAPI] request is None")
            return False

        if success_cb is None:
            Trace.log("Manager", 0, "[PlayFabBaseMethods|callPlayFabAPI] success_cb is None")
            return False

        if fail_cb is None:
            Trace.log("Manager", 0, "[PlayFabBaseMethods|callPlayFabAPI] fail_cb is None")
            return False

        if possible_errors is None:
            Trace.log("Manager", 0, "[PlayFabBaseMethods|callPlayFabAPI] possible_errors is None")
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
            Trace.log("Manager", 0, "[PlayFabBaseMethods|cb_wrap_with_check] cb is None")
            return None

        def __real_decorator(func):
            def __wrapper(response):
                modified_response = func(response)
                cb(modified_response)
            return __wrapper
        return __real_decorator
