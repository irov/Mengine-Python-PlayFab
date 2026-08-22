from Foundation.Task.Task import Task
from PlayFab.PlayFabErrors import PlayFabError


class TaskPlayFabCreateMatchmakingTicket(Task):
    Skiped = True

    def __init__(self):
        super(TaskPlayFabCreateMatchmakingTicket, self).__init__()

        self.give_up_after_second = None
        self.queue_name = None
        self.success_cb = None
        self.fail_cb = None
        self.error_handlers = None
        self.request_chain = None
        self.start_depth = 0
        self.completed = False
        self.active = False
        self.stage = None

    def _onParams(self, params):
        super(TaskPlayFabCreateMatchmakingTicket, self)._onParams(params)

        self.give_up_after_second = params.get("GiveUpAfterSecond")
        self.queue_name = params.get("QueueName")
        self.success_cb = Utils.make_functor(params, "SuccessCb")
        self.fail_cb = Utils.make_functor(params, "FailCb")
        self.error_handlers = params.get("ErrorHandlers", {})

    def _onValidate(self, params):
        super(TaskPlayFabCreateMatchmakingTicket, self)._onValidate(params)

        if self.give_up_after_second is None:
            self.validateFailed(params, "GiveUpAfterSecond is None")

        if self.queue_name is None:
            self.validateFailed(params, "QueueName is None")

        if self.success_cb is None:
            self.validateFailed(params, "SuccessCb is None")

        if self.fail_cb is None:
            self.validateFailed(params, "FailCb is None")

    def _onFastSkip(self):
        return True

    def _onRun(self):
        from PlayFab.PlayFabBaseMethods import PlayFabBaseMethods

        self.active = True
        self.stage = "EntityToken"
        self.start_depth += 1

        try:
            request_chain = PlayFabBaseMethods.startPlayFabEndpoint(
                "TaskPlayFabAuthenticationGetEntityToken",
                {},
                self.__onEntityToken)
        finally:
            self.start_depth -= 1

        if self.completed is True:
            return True

        if request_chain is None or request_chain is False:
            self.invalidTask("Entity token request did not start")

        if self.stage == "EntityToken":
            self.request_chain = request_chain

        return False

    def __onEntityToken(self, response, error):
        if self.active is False or self.completed is True:
            return

        self.request_chain = None

        if error is not None:
            self.__onFail(error)
            return

        entity = response.get("Entity") if isinstance(response, dict) else None
        title_player_id = entity.get("Id") if isinstance(entity, dict) else None

        if title_player_id is None:
            self.__onFail(PlayFabError({
                "code": 400,
                "status": "Invalid Entity Token",
                "error": "InvalidParams",
                "errorCode": 1000,
                "errorMessage": "PlayFab entity token response has no entity id",
            }))
            return

        from PlayFab.PlayFabMultiplayerManager import PlayFabMultiplayerManager

        self.stage = "MatchmakingTicket"
        self.start_depth += 1

        try:
            request_chain = PlayFabMultiplayerManager.callCreateMatchmakingTicket(
                title_player_id,
                self.give_up_after_second,
                self.queue_name,
                self.__onSuccess,
                self.__onFail,
                **self.error_handlers)
        finally:
            self.start_depth -= 1

        if self.completed is True:
            if self.start_depth == 0:
                self.complete()
            return

        if request_chain is None or request_chain is False:
            self.__onFail(PlayFabError())
            return

        self.request_chain = request_chain

    def __onSuccess(self, response):
        self.__complete(self.success_cb, response)

    def __onFail(self, error):
        if isinstance(error, PlayFabError) is False:
            error = PlayFabError(error)

        self.__complete(self.fail_cb, error)

    def __complete(self, cb, value):
        if self.active is False or self.completed is True:
            return

        self.completed = True
        self.request_chain = None

        cb(value)

        if self.start_depth == 0:
            self.complete()

    def _onSkip(self):
        self.active = False

        request_chain = self.request_chain
        self.request_chain = None

        if request_chain is not None:
            request_chain.cancel()

    def _onFinally(self):
        self.active = False
        self.request_chain = None
        self.stage = None
        self.success_cb = None
        self.fail_cb = None
        self.error_handlers = None
