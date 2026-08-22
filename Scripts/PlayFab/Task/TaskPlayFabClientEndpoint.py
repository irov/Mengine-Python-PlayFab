import PlayFab.PlayFabErrors as PlayFabErrors
import PlayFab.PlayFabSettings as PlayFabSettings

from PlayFab.Task.TaskPlayFabHTTPEndpoint import TaskPlayFabHTTPEndpoint


class TaskPlayFabClientEndpoint(TaskPlayFabHTTPEndpoint):
    Skiped = True

    def _getAuthorization(self):
        session_ticket = PlayFabSettings._internalSettings.ClientSessionTicket

        if not session_ticket:
            raise PlayFabErrors.PlayFabException("Must be logged in to call this method")

        return "X-Authorization", session_ticket
