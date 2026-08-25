from PlayFab.Task.TaskPlayFabMultiplayerEndpoint import TaskPlayFabMultiplayerEndpoint


class TaskPlayFabCloudScriptExecuteFunction(TaskPlayFabMultiplayerEndpoint):
    CompleteOnCancel = True
    EndpointPath = "/CloudScript/ExecuteFunction"
