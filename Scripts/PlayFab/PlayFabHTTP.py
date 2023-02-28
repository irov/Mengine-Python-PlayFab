import json
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
        j = json.dumps(request)
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


def __httpResponseHandler(httpResponse, callback):
    error = response = None

    if httpResponse.status_code != 200:
        # Failed to contact PlayFab Case
        error = PlayFabErrors.PlayFabError()

        error.HttpCode = httpResponse.status_code
        error.HttpStatus = httpResponse.reason
    else:
        # Contacted playfab
        responseWrapper = json.loads(httpResponse.content.decode("utf-8"))
        if responseWrapper["code"] != 200:
            # contacted PlayFab, but response indicated failure
            error = responseWrapper
        else:
            # successful call to PlayFab
            response_data = responseWrapper["data"]
            if response_data.get("Error") is not None:
                error_desc = response_data.get("Error")

                error = PlayFabErrors.PlayFabError()

                error.HttpCode = httpResponse.status_code
                error.HttpStatus = httpResponse.reason

                error.Error = error_desc.get("Error")
                error.ErrorCode = PlayFabErrors.PlayFabErrorCode[error_desc.get("Error")]
                error.ErrorMessage = error_desc.get("Message")

                error_details = {}
                for key, value in error_desc.iteritems():
                    error_details[key] = [value]
                logs = response_data.get("Logs")
                if logs:
                    error_details["Logs"] = logs

                error.ErrorDetails = error_details
            else:
                response = response_data

    if error and callback:
        callGlobalErrorHandler(error)
        callback(None, error)
        # try:
        #     # Notify the caller about an API Call failure
        #     callback(None, error)
        # except Exception as e:
        #     # Global notification about exception in caller's callback
        #     PlayFabSettings.GlobalExceptionLogger(e)
    elif response and callback:
        callback(response, None)
        # try:
        #     # Notify the caller about an API Call success
        #     callback(response, None)
        # except Exception as e:
        #     # Global notification about exception in caller's callback
        #     PlayFabSettings.GlobalExceptionLogger(e)
    elif callback:
        callback(None, None)


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
