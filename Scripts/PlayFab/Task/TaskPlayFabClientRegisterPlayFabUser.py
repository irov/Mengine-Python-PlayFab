from PlayFab.Task.TaskPlayFabClientLoginEndpoint import TaskPlayFabClientLoginEndpoint


class TaskPlayFabClientRegisterPlayFabUser(TaskPlayFabClientLoginEndpoint):
    EndpointPath = "/Client/RegisterPlayFabUser"
    UpdateEntityToken = False
