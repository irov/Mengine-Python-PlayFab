import PlayFab.PlayFabErrors as PlayFabErrors
import PlayFab.PlayFabSettings as PlayFabSettings

from PlayFab.Task.TaskPlayFabHTTPEndpoint import TaskPlayFabHTTPEndpoint


class TaskPlayFabMultiplayerEndpoint(TaskPlayFabHTTPEndpoint):
    Skiped = True

    def _getAuthorization(self):
        entity_token = PlayFabSettings._internalSettings.EntityToken

        if not entity_token:
            raise PlayFabErrors.PlayFabException("Must call GetEntityToken before calling this method")

        return "X-EntityToken", entity_token
