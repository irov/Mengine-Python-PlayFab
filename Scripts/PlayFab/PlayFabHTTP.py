import PlayFab.PlayFabErrors as PlayFabErrors
import PlayFab.PlayFabSettings as PlayFabSettings
from Foundation.TaskManager import TaskManager


def DoPost(urlPath, request, authKey, authVal, callback, customData=None, extraHeaders=None):
    """
    Schedule an asynchronous PlayFab HTTP request.
    The callback receives either response data or a PlayFab error envelope.
    Returns the request task chain so its owner can cancel the transport.
    """

    url = PlayFabSettings.GetURL(urlPath, PlayFabSettings._internalSettings.RequestGetParams)

    try:
        j = Mengine.encodeJSON(request)
    except (TypeError, ValueError, OverflowError, RuntimeError) as e:
        raise PlayFabErrors.PlayFabException("The given request is not json serializable. {}".format(e))

    requestHeaders = {}

    if extraHeaders:
        requestHeaders.update(extraHeaders)

    requestHeaders["Content-Type"] = "application/json"
    requestHeaders["X-PlayFabSDK"] = PlayFabSettings._internalSettings.SdkVersionString
    requestHeaders["X-ReportErrorAsSuccess"] = "true"  # Makes processing PlayFab errors a little easier

    if authKey and authVal:
        requestHeaders[authKey] = authVal

    # Mengine http request
    headers = []
    for key, value in requestHeaders.items():  # convert headers dict to list (vector)
        list_header = "{}: {}".format(key, value)
        headers.append(list_header)

    request_completed = [False]

    def __request_cb(_status, error, response, code, successful):
        request_completed[0] = True
        __httpResponseHandler(error, response, code, successful, callback)

    def __request_finished():
        if request_completed[0] is True:
            return

        __request_cb(None, "Request Not Started", "", 408, False)

    request_chain = TaskManager.createTaskChain()

    with request_chain as source:
        source.addTask("TaskPlayFabRequest", Url=url, Headers=headers, Data=j, Cb=__request_cb)
        source.addFunction(__request_finished)

    return request_chain


def __makeError(http_code, http_status, error, error_code, error_message, error_details=None, transport_error=False):
    return {
        "code": http_code,
        "status": http_status,
        "error": error,
        "errorCode": error_code,
        "errorMessage": error_message,
        "errorDetails": error_details,
        "transportError": transport_error,
    }


def __makeTransportError(http_code, http_status):
    if http_code is None or http_code <= 0:
        http_code = 408

    return __makeError(
        http_code,
        http_status,
        "ServiceUnavailable",
        1123,
        "Unable to contact PlayFab server",
        transport_error=True)


def __decodeResponse(reason, response, code, successful):
    if successful is False:
        return None, __makeTransportError(code, reason or "Transport Error")

    response_text = response or ""

    if code != 200:
        if response_text:
            try:
                response_wrapper = Mengine.decodeJSON(response_text)
            except (ValueError, OverflowError):
                response_wrapper = None

            if isinstance(response_wrapper, dict) and response_wrapper.get("error") is not None:
                error = __makeError(
                    response_wrapper.get("code", code),
                    response_wrapper.get("status", reason or "PlayFab Error"),
                    response_wrapper.get("error", "UnknownError"),
                    response_wrapper.get("errorCode", 1),
                    response_wrapper.get("errorMessage", "PlayFab request failed"),
                    response_wrapper.get("errorDetails"))

                return None, error

        error = __makeError(
            code,
            reason or "HTTP Error",
            "HttpRequestError",
            1,
            reason or "PlayFab request failed")

        return None, error

    if not response_text:
        return {}, None

    try:
        response_wrapper = Mengine.decodeJSON(response_text)
    except (ValueError, OverflowError):
        error = __makeError(
            code,
            reason or "Invalid Response",
            "JsonParseError",
            3,
            "PlayFab returned invalid JSON")

        return None, error

    if isinstance(response_wrapper, dict) is False:
        error = __makeError(
            code,
            reason or "Invalid Response",
            "JsonParseError",
            3,
            "PlayFab returned an invalid response envelope")

        return None, error

    if response_wrapper.get("code") != 200 or response_wrapper.get("error") is not None:
        error = __makeError(
            response_wrapper.get("code", code),
            response_wrapper.get("status", reason or "PlayFab Error"),
            response_wrapper.get("error", "UnknownError"),
            response_wrapper.get("errorCode", 1),
            response_wrapper.get("errorMessage", "PlayFab request failed"),
            response_wrapper.get("errorDetails"))

        return None, error

    response_data = response_wrapper.get("data")

    if response_data is None:
        response_data = {}

    if isinstance(response_data, dict) and response_data.get("Error") is not None:
        error_desc = response_data.get("Error")

        if isinstance(error_desc, dict) is False:
            error_desc = {}

        error_details = {}

        for key, value in error_desc.items():
            error_details[key] = [value]

        logs = response_data.get("Logs")

        if logs:
            error_details["Logs"] = logs

        error = __makeError(
            code,
            reason or "CloudScript Error",
            error_desc.get("Error", "CloudScriptAPIRequestError"),
            1210,
            error_desc.get("Message", "CloudScript execution failed"),
            error_details)

        return None, error

    return response_data, None


def __httpResponseHandler(reason, response, code, successful, callback):
    response, error = __decodeResponse(reason, response, code, successful)

    __dispatchResponse(response, error, callback)


def __dispatchResponse(response, error, callback):
    if error is not None:
        callGlobalErrorHandler(error)

    if callback is None:
        return

    callback(response, error)


def callGlobalErrorHandler(error):
    if PlayFabSettings.GlobalErrorHandler:
        # Global notification about an API Call failure
        PlayFabSettings.GlobalErrorHandler(error)
