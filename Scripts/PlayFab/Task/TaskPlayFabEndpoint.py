from Foundation.Task.Task import Task


class TaskPlayFabEndpoint(Task):
    Skiped = True

    def __init__(self):
        super(TaskPlayFabEndpoint, self).__init__()

        self.request = None
        self.cb = None
        self.request_chain = None
        self.in_run = False
        self.response_received = False
        self.active = False

    def _runEndpoint(self, request, callback):
        raise NotImplementedError("PlayFab endpoint is not implemented")

    def _onEndpointResponse(self, response, error):
        pass

    def _onParams(self, params):
        super(TaskPlayFabEndpoint, self)._onParams(params)

        self.request = params.get("Request")
        self.cb = Utils.make_functor(params, "Cb")

    def _onValidate(self, params):
        super(TaskPlayFabEndpoint, self)._onValidate(params)

        if self.request is None:
            self.validateFailed(params, "Request is None")

        if self.cb is None:
            self.validateFailed(params, "Cb is None")

    def _onFastSkip(self):
        return True

    def _onRun(self):
        self.active = True
        self.in_run = True

        try:
            request_chain = self._runEndpoint(self.request, self.__onResponse)
        finally:
            self.in_run = False

        if self.response_received is True:
            return True

        if request_chain is None:
            self.invalidTask("PlayFab endpoint did not return a request handle")

        self.request_chain = request_chain

        return False

    def __onResponse(self, response, error):
        if self.active is False or self.response_received is True:
            return

        self.response_received = True
        self.request_chain = None

        self._onEndpointResponse(response, error)
        self.cb(response, error)

        if self.in_run is False:
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
        self.request = None
        self.cb = None
