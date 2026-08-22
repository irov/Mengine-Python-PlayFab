import PlayFab.PlayFabSettings as PlayFabSettings

from PlayFab.Task.TaskPlayFabHTTPEndpoint import TaskPlayFabHTTPEndpoint


class TaskPlayFabAuthenticationGetEntityToken(TaskPlayFabHTTPEndpoint):
    EndpointPath = "/Authentication/GetEntityToken"

    def _getAuthorization(self):
        auth_key = None
        auth_value = None

        if PlayFabSettings._internalSettings.EntityToken:
            auth_key = "X-EntityToken"
            auth_value = PlayFabSettings._internalSettings.EntityToken
        elif PlayFabSettings._internalSettings.ClientSessionTicket:
            auth_key = "X-Authorization"
            auth_value = PlayFabSettings._internalSettings.ClientSessionTicket
        elif PlayFabSettings.DeveloperSecretKey:
            auth_key = "X-SecretKey"
            auth_value = PlayFabSettings.DeveloperSecretKey

        return auth_key, auth_value

    def _onEndpointResponse(self, response, error):
        if response and "EntityToken" in response:
            PlayFabSettings._internalSettings.EntityToken = response["EntityToken"]
