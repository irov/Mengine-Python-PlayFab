import PlayFab.PlayFabErrors as PlayFabErrors
import PlayFab.PlayFabSettings as PlayFabSettings

from PlayFab.Task.TaskPlayFabHTTPEndpoint import TaskPlayFabHTTPEndpoint


class TaskPlayFabClientLoginEndpoint(TaskPlayFabHTTPEndpoint):
    Skiped = True
    UpdateEntityToken = True

    def _validateEndpointRequest(self, request):
        request["TitleId"] = PlayFabSettings.TitleId or request.get("TitleId")

        if not request["TitleId"]:
            raise PlayFabErrors.PlayFabException("Must have TitleId set to call this method")

    def _onEndpointResponse(self, response, error):
        if not response:
            return

        if "SessionTicket" in response:
            PlayFabSettings._internalSettings.ClientSessionTicket = response["SessionTicket"]

        if self.UpdateEntityToken is True and "EntityToken" in response:
            PlayFabSettings._internalSettings.EntityToken = response["EntityToken"]["EntityToken"]
