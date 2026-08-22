from Foundation.DefaultManager import DefaultManager
from Foundation.TaskManager import TaskManager
from PlayFab.PlayFabErrors import PlayFabError


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
    def makePlayFabEndpointCb(task_name, success_cb, fail_cb, error_handlers):
        DebugPlayFabLogOnSuccess = DefaultManager.getDefault("DebugPlayFabLogOnSuccess", False)
        DebugPlayFabLogOnFail = DefaultManager.getDefault("DebugPlayFabLogOnFail", False)

        def __cb(response, error):
            if error is not None:
                if DebugPlayFabLogOnFail:
                    PlayFabBaseMethods.print_data("[PlayFab] '{}' call - ERROR".format(task_name), error)
                if isinstance(error, PlayFabError) is False:
                    playFabError = PlayFabError(error)
                else:
                    playFabError = error
                error_handler = error_handlers.get(playFabError.Error) or fail_cb

                error_handler(playFabError)

                return

            if response is not None:
                if DebugPlayFabLogOnSuccess:
                    PlayFabBaseMethods.print_data("[PlayFab] '{}' call - RESPONSE".format(task_name), response)
                success_cb(response)

                return

            if DebugPlayFabLogOnSuccess:
                PlayFabBaseMethods.print_data("[PlayFab] '{}' call - EMPTY RESPONSE".format(task_name), {})

            success_cb({})

        return __cb

    @staticmethod
    def checkPlayFabEndpoint(task_name, request, success_cb, fail_cb, possible_errors, error_handlers):
        if not task_name:
            Trace.log("Manager", 0, "[PlayFab|checkPlayFabEndpoint] task_name is empty")
            return False

        if request is None:
            Trace.log("Manager", 0, "[PlayFab|checkPlayFabEndpoint] request is None")
            return False

        if success_cb is None:
            Trace.log("Manager", 0, "[PlayFab|checkPlayFabEndpoint] success_cb is None")
            return False

        if fail_cb is None:
            Trace.log("Manager", 0, "[PlayFab|checkPlayFabEndpoint] fail_cb is None")
            return False

        if possible_errors is None:
            Trace.log("Manager", 0, "[PlayFab|checkPlayFabEndpoint] possible_errors is None")
            return False

        DebugPlayFabLogErrorHandlerCheck = DefaultManager.getDefault("DebugPlayFabLogErrorHandlerCheck", False)

        for error_name in possible_errors:
            PlayFabBaseMethods.checkErrorHandler(error_name, error_handlers, log=DebugPlayFabLogErrorHandlerCheck)

        return True

    @staticmethod
    def preparePlayFabEndpoint(task_name, request, success_cb, fail_cb, possible_errors, error_handlers):
        if PlayFabBaseMethods.checkPlayFabEndpoint(
                task_name,
                request,
                success_cb,
                fail_cb,
                possible_errors,
                error_handlers) is False:
            return

        endpoint_cb = PlayFabBaseMethods.makePlayFabEndpointCb(task_name, success_cb, fail_cb, error_handlers)

        return task_name, request, endpoint_cb

    @staticmethod
    def startPlayFabEndpoint(task_name, request, cb):
        request_chain = TaskManager.createTaskChain()

        with request_chain as source:
            source.addTask(task_name, Request=request, Cb=cb)

        return request_chain

    @staticmethod
    def callPlayFabEndpoint(endpoint_prepare_method, *args, **kwargs):
        prepared_endpoint = endpoint_prepare_method(*args, **kwargs)

        if prepared_endpoint is None:
            return False

        task_name, request, endpoint_cb = prepared_endpoint
        callback_called = [False]

        def __callback(response, error):
            if callback_called[0] is True:
                return

            callback_called[0] = True
            endpoint_cb(response, error)

        return PlayFabBaseMethods.startPlayFabEndpoint(
            task_name,
            request,
            __callback)

    @staticmethod
    def scopePlayFabEndpoint(source, endpoint_prepare_method, *args, **kwargs):
        prepared_endpoint = endpoint_prepare_method(*args, **kwargs)

        if prepared_endpoint is None:
            Trace.log("Manager", 0, "[PlayFab|scopePlayFabEndpoint] invalid prepared endpoint")

            return

        task_name, request, endpoint_cb = prepared_endpoint

        source.addTask(
            task_name,
            Request=request,
            Cb=endpoint_cb)

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
