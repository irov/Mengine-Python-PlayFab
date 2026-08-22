from Foundation.Task.Task import Task


class TaskPlayFabPlatformLogin(Task):
    Skiped = True

    def __init__(self):
        super(TaskPlayFabPlatformLogin, self).__init__()

        self.success_cb = None
        self.fallback_cb = None
        self.fail_cb = None
        self.identity_request_id = None
        self.request_chain = None
        self.start_depth = 0
        self.completed = False
        self.active = False
        self.stage = None

    def _onParams(self, params):
        super(TaskPlayFabPlatformLogin, self)._onParams(params)

        self.success_cb = Utils.make_functor(params, "SuccessCb")
        self.fallback_cb = Utils.make_functor(params, "FallbackCb")
        self.fail_cb = Utils.make_functor(params, "FailCb")

    def _onValidate(self, params):
        super(TaskPlayFabPlatformLogin, self)._onValidate(params)

        if self.success_cb is None:
            self.validateFailed(params, "SuccessCb is None")

        if self.fallback_cb is None:
            self.validateFailed(params, "FallbackCb is None")

        if self.fail_cb is None:
            self.validateFailed(params, "FailCb is None")

    def _onFastSkip(self):
        return True

    def _onRun(self):
        from PlayFab.PlayFabManager import PlayFabManager

        self.active = True
        self.stage = "Identity"
        self.start_depth += 1

        try:
            identity_request_id = PlayFabManager.requestPlatformIdentity(
                self.__onIdentitySuccess,
                self.__onLoginFallback,
                self.__onLoginFallback)
        finally:
            self.start_depth -= 1

        if self.completed is True:
            return True

        if identity_request_id is None or identity_request_id is False:
            self.invalidTask("Platform identity request did not start")

        if self.stage == "Identity":
            self.identity_request_id = identity_request_id

        return False

    def __onIdentitySuccess(self, identity):
        if self.active is False or self.completed is True:
            return

        from PlayFab.PlayFabManager import PlayFabManager

        self.identity_request_id = None
        self.stage = "Login"

        provider = identity.get("Provider")
        credential = identity.get("Credential")

        self.start_depth += 1

        try:
            if provider == "GooglePlayGames":
                error_handlers = dict((error, self.__onLoginFallback) for error in [
                    "AccountNotFound",
                    "GoogleOAuthError",
                    "GoogleOAuthNotConfiguredForTitle",
                    "InvalidGooglePlayGamesServerAuthCode",
                    "InvalidGoogleToken",
                    "InvalidTitleId",
                ])
                request_chain = PlayFabManager.callLoginWithGooglePlayGamesServices(
                    credential,
                    False,
                    self.__onLoginSuccess,
                    self.__onLoginFailed,
                    **error_handlers)
            elif provider == "GameCenter":
                error_handlers = dict((error, self.__onLoginFallback) for error in [
                    "AccountNotFound",
                    "GameCenterAuthenticationFailed",
                    "InvalidGameCenterAuthRequest",
                    "InvalidTitleId",
                ])
                request_chain = PlayFabManager.callLoginWithGameCenter(
                    credential,
                    False,
                    self.__onLoginSuccess,
                    self.__onLoginFailed,
                    **error_handlers)
            else:
                self.__onLoginFallback("UnsupportedPlatformIdentity")
                request_chain = None
        finally:
            self.start_depth -= 1

        if self.completed is True:
            if self.start_depth == 0:
                self.complete()
            return

        if request_chain is None or request_chain is False:
            self.__onLoginFallback("PlatformLoginNotStarted")
            return

        self.request_chain = request_chain

    def __onLoginSuccess(self, response):
        self.__complete(self.success_cb, response)

    def __onLoginFallback(self, reason):
        self.__complete(self.fallback_cb, reason)

    def __onLoginFailed(self, error):
        self.__complete(self.fail_cb, error)

    def __complete(self, cb, value):
        if self.active is False or self.completed is True:
            return

        self.completed = True
        self.identity_request_id = None
        self.request_chain = None

        cb(value)

        if self.start_depth == 0:
            self.complete()

    def _onSkip(self):
        self.active = False

        identity_request_id = self.identity_request_id
        self.identity_request_id = None

        if identity_request_id is not None:
            from PlayFab.PlayFabManager import PlayFabManager
            PlayFabManager.cancelPlatformIdentityRequest(identity_request_id)

        request_chain = self.request_chain
        self.request_chain = None

        if request_chain is not None:
            request_chain.cancel()

    def _onFinally(self):
        self.active = False
        self.identity_request_id = None
        self.request_chain = None
        self.stage = None
        self.success_cb = None
        self.fallback_cb = None
        self.fail_cb = None
