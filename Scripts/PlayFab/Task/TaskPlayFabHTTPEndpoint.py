import PlayFab.PlayFabHTTP as PlayFabHTTP

from PlayFab.Task.TaskPlayFabEndpoint import TaskPlayFabEndpoint


class TaskPlayFabHTTPEndpoint(TaskPlayFabEndpoint):
    Skiped = True
    EndpointPath = None

    def _validateEndpointRequest(self, request):
        pass

    def _getAuthorization(self):
        return None, None

    def _runEndpoint(self, request, callback):
        if not self.EndpointPath:
            raise RuntimeError("PlayFab endpoint path is empty")

        self._validateEndpointRequest(request)

        auth_key, auth_value = self._getAuthorization()

        return PlayFabHTTP.DoPost(
            self.EndpointPath,
            request,
            auth_key,
            auth_value,
            callback)
