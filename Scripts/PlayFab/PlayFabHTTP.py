import PlayFab.PlayFabErrors as PlayFabErrors
import PlayFab.PlayFabSettings as PlayFabSettings
from Foundation.TaskManager import TaskManager


def DoPost(urlPath, request, authKey, authVal, callback, customData=None, extraHeaders=None):
    """
    Note this is a blocking call and will always run synchronously
    the return type is a dictionary that should contain a valid dictionary that
    should reflect the expected JSON response
    if the call fails, there will be a returned PlayFabError
    """

    url = PlayFabSettings.GetURL(urlPath, PlayFabSettings._internalSettings.RequestGetParams)

    try:
        j = Mengine.encodeJSON(request)
    except Exception as e:
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

    with TaskManager.createTaskChain() as source:
        source.addTask("TaskHeaderData", Url=url, Headers=headers, Data=j, Cb=__onHeaderData, Args=(callback,))


def __makeError(http_code, http_status, error, error_code, error_message, error_details=None):
    return {
        "code": http_code,
        "status": http_status,
        "error": error,
        "errorCode": error_code,
        "errorMessage": error_message,
        "errorDetails": error_details,
    }


def __decodeResponse(httpResponse):
    response_text = httpResponse.content.decode("utf-8")

    if httpResponse.status_code != 200:
        if response_text:
            try:
                response_wrapper = Mengine.decodeJSON(response_text)

                if isinstance(response_wrapper, dict) and response_wrapper.get("error") is not None:
                    error = __makeError(
                        response_wrapper.get("code", httpResponse.status_code),
                        response_wrapper.get("status", httpResponse.reason or "PlayFab Error"),
                        response_wrapper.get("error", "UnknownError"),
                        response_wrapper.get("errorCode", 1),
                        response_wrapper.get("errorMessage", "PlayFab request failed"),
                        response_wrapper.get("errorDetails"))

                    return None, error
            except Exception:
                pass

        error = __makeError(
            httpResponse.status_code,
            httpResponse.reason or "Transport Error",
            "ServiceUnavailable",
            1123,
            "Unable to contact PlayFab server")

        return None, error

    if not response_text:
        return {}, None

    try:
        response_wrapper = Mengine.decodeJSON(response_text)
    except Exception:
        error = __makeError(
            httpResponse.status_code,
            httpResponse.reason or "Invalid Response",
            "JsonParseError",
            3,
            "PlayFab returned invalid JSON")

        return None, error

    if isinstance(response_wrapper, dict) is False:
        error = __makeError(
            httpResponse.status_code,
            httpResponse.reason or "Invalid Response",
            "JsonParseError",
            3,
            "PlayFab returned an invalid response envelope")

        return None, error

    if response_wrapper.get("code") != 200 or response_wrapper.get("error") is not None:
        error = __makeError(
            response_wrapper.get("code", httpResponse.status_code),
            response_wrapper.get("status", httpResponse.reason or "PlayFab Error"),
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
            httpResponse.status_code,
            httpResponse.reason or "CloudScript Error",
            error_desc.get("Error", "CloudScriptAPIRequestError"),
            1210,
            error_desc.get("Message", "CloudScript execution failed"),
            error_details)

        return None, error

    return response_data, None


def __httpResponseHandler(httpResponse, callback):
    response, error = __decodeResponse(httpResponse)

    if error is not None:
        callGlobalErrorHandler(error)

        if callback:
            callback(None, error)

        return

    if callback:
        callback(response, None)


class HttpResponseAdapter(object):
    class Content(object):
        def __init__(self, response):
            self.response = response

        def decode(self, encoding):
            return self.response

    def __init__(self, error, response, code):
        self.status_code = code
        self.reason = error
        self.content = HttpResponseAdapter.Content(response)


def __onHeaderData(status, error, response, code, successful, callback):
    httpResponse = HttpResponseAdapter(error, response, code)

    __httpResponseHandler(httpResponse, callback)


def callGlobalErrorHandler(error):
    if PlayFabSettings.GlobalErrorHandler:
        try:
            # Global notification about an API Call failure
            PlayFabSettings.GlobalErrorHandler(error)
        except Exception as e:
            # Global notification about exception in caller's callback
            PlayFabSettings.GlobalExceptionLogger(e)
