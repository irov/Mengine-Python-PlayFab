from Foundation.DefaultManager import DefaultManager
from Foundation.Providers.AnalyticsProvider import AnalyticsProvider
from PlayFab.PlayFabErrors import PlayFabError
from PlayFab.PlayFabManager import PlayFabManager
import PlayFab.PlayFabHTTP as PlayFabHTTP


class PlayFabAccountDeletion(object):
    STATE_IDLE = "idle"
    STATE_REQUESTING = "requesting"
    STATE_AMBIGUOUS = "ambiguous"
    STATE_DELETING = "deleting"

    SETTING_STATE = "PlayFabDeleteState"
    SETTING_REQUEST_ID = "PlayFabDeleteRequestId"
    SETTING_REQUESTED_AT = "PlayFabDeleteRequestedAt"

    DEFAULT_FUNCTION_NAME = "DeleteMasterPlayerAccount"

    s_initialized = False
    s_dialog_open = False
    s_busy = False
    s_generation = 0
    s_request_chain = None
    s_account_deleted_handled = False

    @staticmethod
    def initialize():
        if PlayFabAccountDeletion.s_initialized is True:
            return

        PlayFabAccountDeletion.s_initialized = True
        PlayFabHTTP.addGlobalErrorHandler(PlayFabAccountDeletion.__onGlobalPlayFabError)

    @staticmethod
    def finalize():
        if PlayFabAccountDeletion.s_initialized is False:
            return

        PlayFabAccountDeletion.s_initialized = False
        PlayFabHTTP.removeGlobalErrorHandler(PlayFabAccountDeletion.__onGlobalPlayFabError)

        PlayFabAccountDeletion.s_generation += 1
        PlayFabAccountDeletion.s_dialog_open = False
        PlayFabAccountDeletion.s_busy = False
        PlayFabAccountDeletion.s_account_deleted_handled = False

        request_chain = PlayFabAccountDeletion.s_request_chain
        PlayFabAccountDeletion.s_request_chain = None

        if request_chain is not None:
            request_chain.cancel()

    @staticmethod
    def onAccountsLoaded():
        PlayFabAccountDeletion.s_account_deleted_handled = False
        PlayFabAccountDeletion.promoteStaleRequest()

    @staticmethod
    def setupAccountSettings():
        Mengine.addCurrentAccountSetting(
            PlayFabAccountDeletion.SETTING_STATE,
            unicode(PlayFabAccountDeletion.STATE_IDLE),
            None)
        Mengine.addCurrentAccountSetting(
            PlayFabAccountDeletion.SETTING_REQUEST_ID,
            u"",
            None)
        Mengine.addCurrentAccountSetting(
            PlayFabAccountDeletion.SETTING_REQUESTED_AT,
            u"0",
            None)

    @staticmethod
    def __hasSetting(name):
        return Mengine.hasCurrentAccountSetting(name) is True

    @staticmethod
    def __getSetting(name, default=""):
        if PlayFabAccountDeletion.__hasSetting(name) is False:
            return default

        value = Mengine.getCurrentAccountSetting(name)

        if value is None:
            return default

        return str(value)

    @staticmethod
    def __saveState(state, request_id=None, requested_at=None):
        settings = {
            PlayFabAccountDeletion.SETTING_STATE: state,
        }

        if request_id is not None:
            settings[PlayFabAccountDeletion.SETTING_REQUEST_ID] = request_id

        if requested_at is not None:
            settings[PlayFabAccountDeletion.SETTING_REQUESTED_AT] = requested_at

        for name in settings:
            if PlayFabAccountDeletion.__hasSetting(name) is False:
                Mengine.logError("[PlayFab] Missing account deletion setting '{}'".format(name))
                return False

        for name, value in settings.items():
            if Mengine.changeCurrentAccountSetting(name, unicode(value)) is False:
                Mengine.logError("[PlayFab] Failed to change account deletion setting '{}'".format(name))
                return False

        Mengine.saveAccounts()

        return True

    @staticmethod
    def __resetState():
        return PlayFabAccountDeletion.__saveState(
            PlayFabAccountDeletion.STATE_IDLE,
            "",
            "0")

    @staticmethod
    def getState():
        return PlayFabAccountDeletion.__getSetting(
            PlayFabAccountDeletion.SETTING_STATE,
            PlayFabAccountDeletion.STATE_IDLE)

    @staticmethod
    def hasPendingRequest():
        state = PlayFabAccountDeletion.getState()

        if state not in (PlayFabAccountDeletion.STATE_REQUESTING, PlayFabAccountDeletion.STATE_AMBIGUOUS):
            return False

        request_id = PlayFabAccountDeletion.__getSetting(PlayFabAccountDeletion.SETTING_REQUEST_ID)

        return bool(request_id)

    @staticmethod
    def isRegistrationBlocked():
        state = PlayFabAccountDeletion.getState()

        return state in (
            PlayFabAccountDeletion.STATE_REQUESTING,
            PlayFabAccountDeletion.STATE_AMBIGUOUS,
            PlayFabAccountDeletion.STATE_DELETING,
        )

    @staticmethod
    def promoteStaleRequest():
        state = PlayFabAccountDeletion.getState()

        if state == PlayFabAccountDeletion.STATE_IDLE or state == PlayFabAccountDeletion.STATE_DELETING:
            return

        if state not in (PlayFabAccountDeletion.STATE_REQUESTING, PlayFabAccountDeletion.STATE_AMBIGUOUS):
            PlayFabAccountDeletion.__resetState()
            return

        request_id = PlayFabAccountDeletion.__getSetting(PlayFabAccountDeletion.SETTING_REQUEST_ID)

        if request_id:
            PlayFabAccountDeletion.__saveState(PlayFabAccountDeletion.STATE_AMBIGUOUS)
        else:
            PlayFabAccountDeletion.__saveState(
                PlayFabAccountDeletion.STATE_DELETING,
                "",
                "0")

    @staticmethod
    def __analytics(status):
        AnalyticsProvider.sendAnalytic("delete_account_result", {"status": status})

    @staticmethod
    def __getErrorName(error):
        if isinstance(error, dict) is True:
            return error.get("error")

        return getattr(error, "Error", error)

    @staticmethod
    def __onGlobalPlayFabError(error):
        if PlayFabAccountDeletion.__getErrorName(error) != "AccountDeleted":
            return False

        playfab_error = PlayFabError(error) if isinstance(error, dict) is True else error

        return PlayFabAccountDeletion.handleAuthenticationError(playfab_error)

    @staticmethod
    def __completeResult(result):
        try:
            if Mengine.completeDeleteAccount(result) is True:
                return True
        except Exception as ex:
            Trace.log_exception("PlayFab", 0, "Delete account native result failed: %s" % ex)

        if result in (Mengine.DELETE_ACCOUNT_RESULT_ACCEPTED, Mengine.DELETE_ACCOUNT_RESULT_COMPLETED):
            Mengine.removeUserData()
            Mengine.quitApplication()
        elif result == Mengine.DELETE_ACCOUNT_RESULT_PENDING:
            Mengine.quitApplication()
        else:
            Mengine.logError("[PlayFab] Unable to show account deletion result: {}".format(result))

        return False

    @staticmethod
    def openDeleteAccountFlow():
        if PlayFabAccountDeletion.s_dialog_open is True or PlayFabAccountDeletion.s_busy is True:
            return False

        if PlayFabAccountDeletion.getState() == PlayFabAccountDeletion.STATE_DELETING:
            PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_PENDING)
            return True

        def __accepted():
            if PlayFabAccountDeletion.s_dialog_open is False:
                return

            PlayFabAccountDeletion.s_dialog_open = False
            AnalyticsProvider.sendAnalytic("delete_account_confirmed", {})
            PlayFabAccountDeletion.requestDeletion()

        def __canceled():
            if PlayFabAccountDeletion.s_dialog_open is False:
                return

            PlayFabAccountDeletion.s_dialog_open = False
            AnalyticsProvider.sendAnalytic("delete_account_canceled", {})

        PlayFabAccountDeletion.s_dialog_open = True

        try:
            shown = Mengine.openDeleteAccount(__accepted, __canceled)
        except Exception as ex:
            Trace.log_exception("PlayFab", 0, "Delete account dialog failed to open: %s" % ex)
            shown = False

        if shown is False:
            PlayFabAccountDeletion.s_dialog_open = False
            PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_SERVER_ERROR)
            return False

        return True

    @staticmethod
    def requestDeletion():
        if PlayFabAccountDeletion.s_busy is True:
            return False

        if PlayFabAccountDeletion.getState() == PlayFabAccountDeletion.STATE_DELETING:
            PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_PENDING)
            return False

        pending = PlayFabAccountDeletion.hasPendingRequest()

        if pending is True:
            request_id = PlayFabAccountDeletion.__getSetting(PlayFabAccountDeletion.SETTING_REQUEST_ID)
            requested_at = PlayFabAccountDeletion.__getSetting(
                PlayFabAccountDeletion.SETTING_REQUESTED_AT,
                "0")
        else:
            request_id = str(Mengine.generateUniqueIdentity(64))
            requested_at = str(Mengine.getTimeMs())

        if Mengine.isNetworkAvailable() is False:
            if pending is True:
                PlayFabAccountDeletion.__saveState(PlayFabAccountDeletion.STATE_AMBIGUOUS)
            else:
                PlayFabAccountDeletion.__resetState()

            PlayFabAccountDeletion.__analytics("offline")
            PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_OFFLINE)

            return False

        if PlayFabAccountDeletion.__saveState(
                PlayFabAccountDeletion.STATE_REQUESTING,
                request_id,
                requested_at) is False:
            PlayFabAccountDeletion.__analytics("persistence_error")
            PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_SERVER_ERROR)
            return False

        PlayFabAccountDeletion.s_busy = True
        PlayFabAccountDeletion.s_generation += 1
        generation = PlayFabAccountDeletion.s_generation

        def __token_success(response):
            PlayFabAccountDeletion.__onEntityToken(generation, request_id)

        def __request_failed(error):
            PlayFabAccountDeletion.__onRequestFailed(generation, error, False)

        try:
            request_chain = PlayFabManager.callGetFreshEntityToken(
                __token_success,
                __request_failed)
        except Exception as ex:
            Trace.log_exception("PlayFab", 0, "Delete account EntityToken request failed to start: %s" % ex)
            PlayFabAccountDeletion.__onRequestFailed(generation, None, False)
            return False

        return PlayFabAccountDeletion.__trackRequestChain(generation, request_chain)

    @staticmethod
    def __trackRequestChain(generation, request_chain):
        if request_chain is False or request_chain is None:
            PlayFabAccountDeletion.__onRequestFailed(generation, None, False)
            return False

        if generation == PlayFabAccountDeletion.s_generation and PlayFabAccountDeletion.s_busy is True:
            PlayFabAccountDeletion.s_request_chain = request_chain

        return True

    @staticmethod
    def __onEntityToken(generation, request_id):
        if generation != PlayFabAccountDeletion.s_generation or PlayFabAccountDeletion.s_busy is False:
            return

        def __success(function_result):
            PlayFabAccountDeletion.__onDeleteResult(generation, function_result)

        def __failed(error):
            PlayFabAccountDeletion.__onRequestFailed(generation, error, True)

        function_name = DefaultManager.getDefault(
            "PlayFabDeleteAccountFunctionName",
            PlayFabAccountDeletion.DEFAULT_FUNCTION_NAME)

        if not function_name:
            function_name = PlayFabAccountDeletion.DEFAULT_FUNCTION_NAME

        try:
            request_chain = PlayFabManager.callExecuteFunction(
                function_name,
                {
                    "RequestId": request_id,
                },
                __success,
                __failed)
        except Exception as ex:
            Trace.log_exception("PlayFab", 0, "Delete account ExecuteFunction failed to start: %s" % ex)
            PlayFabAccountDeletion.__onRequestFailed(generation, None, False)
            return

        PlayFabAccountDeletion.__trackRequestChain(generation, request_chain)

    @staticmethod
    def __claimRequest(generation):
        if generation != PlayFabAccountDeletion.s_generation or PlayFabAccountDeletion.s_busy is False:
            return False

        PlayFabAccountDeletion.s_busy = False
        PlayFabAccountDeletion.s_request_chain = None

        return True

    @staticmethod
    def __onDeleteResult(generation, function_result):
        if PlayFabAccountDeletion.__claimRequest(generation) is False:
            return

        valid_result = isinstance(function_result, dict)
        status = function_result.get("Status") if valid_result is True else None

        if status == "Ambiguous":
            PlayFabAccountDeletion.__completeAmbiguousResult()
            return

        if status == "Rejected":
            PlayFabAccountDeletion.__completeServerError("rejected")
            return

        receipt = function_result.get("JobReceiptId") if valid_result is True else None
        title_ids = function_result.get("TitleIds") if valid_result is True else None

        valid_receipt = isinstance(receipt, basestring) is True and bool(receipt.strip())
        valid_title_ids = isinstance(title_ids, list) is True \
            and len(title_ids) != 0 \
            and all(isinstance(title_id, basestring) is True and bool(title_id.strip()) for title_id in title_ids)

        if status != "Accepted" or valid_receipt is False or valid_title_ids is False:
            PlayFabAccountDeletion.__completeServerError("malformed_response")
            return

        PlayFabAccountDeletion.__analytics("accepted")
        PlayFabManager.clearAuthentication()
        PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_ACCEPTED)

    @staticmethod
    def __completeAmbiguousResult():
        PlayFabAccountDeletion.__saveState(PlayFabAccountDeletion.STATE_AMBIGUOUS)
        PlayFabAccountDeletion.__analytics("ambiguous")
        PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_AMBIGUOUS)

    @staticmethod
    def __completeServerError(analytics_status):
        PlayFabAccountDeletion.__resetState()
        PlayFabAccountDeletion.__analytics(analytics_status)
        PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_SERVER_ERROR)

    @staticmethod
    def __onRequestFailed(generation, error, execute_function_started):
        if PlayFabAccountDeletion.__claimRequest(generation) is False:
            return

        if PlayFabAccountDeletion.__getErrorName(error) == "AccountDeleted":
            PlayFabAccountDeletion.handleAuthenticationError(error)
            return

        error_name = PlayFabAccountDeletion.__getErrorName(error)
        transport_error = getattr(error, "TransportError", False) is True

        if isinstance(error, dict) is True:
            transport_error = error.get("transportError", False) is True

        ambiguous_error = transport_error is True or error_name in ("Timeout", "RequestCanceled")

        if ambiguous_error is True:
            PlayFabAccountDeletion.__completeAmbiguousResult()
            return

        analytics_status = "server" if execute_function_started is True else "request_not_started"
        PlayFabAccountDeletion.__completeServerError(analytics_status)

    @staticmethod
    def resumePendingAfterAuthentication():
        state = PlayFabAccountDeletion.getState()

        if state == PlayFabAccountDeletion.STATE_DELETING:
            PlayFabManager.clearAuthentication()
            PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_PENDING)
            return True

        if PlayFabAccountDeletion.hasPendingRequest() is False:
            return False

        PlayFabAccountDeletion.requestDeletion()

        return True

    @staticmethod
    def handleAuthenticationAccountNotFound():
        if PlayFabAccountDeletion.isRegistrationBlocked() is False:
            return False

        PlayFabAccountDeletion.__analytics("completed")
        PlayFabManager.clearAuthentication()
        PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_COMPLETED)

        return True

    @staticmethod
    def handleAuthenticationError(error):
        if PlayFabAccountDeletion.__getErrorName(error) != "AccountDeleted":
            return False

        if PlayFabAccountDeletion.s_account_deleted_handled is True:
            return True

        PlayFabAccountDeletion.s_account_deleted_handled = True

        if PlayFabAccountDeletion.hasPendingRequest() is True:
            PlayFabAccountDeletion.__saveState(PlayFabAccountDeletion.STATE_AMBIGUOUS)
        else:
            PlayFabAccountDeletion.__saveState(
                PlayFabAccountDeletion.STATE_DELETING,
                "",
                "0")

        PlayFabManager.clearAuthentication()
        PlayFabAccountDeletion.__analytics("account_deleted")
        PlayFabAccountDeletion.__completeResult(Mengine.DELETE_ACCOUNT_RESULT_PENDING)

        return True
