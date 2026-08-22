import PlayFab.PlayFabSettings as PlayFabSettings

from PlayFab.Task.TaskPlayFabClientEndpoint import TaskPlayFabClientEndpoint


class TaskPlayFabClientAttributeInstall(TaskPlayFabClientEndpoint):
    EndpointPath = "/Client/AttributeInstall"

    def _onEndpointResponse(self, response, error):
        PlayFabSettings.AdvertisingIdType += "_Successful"
