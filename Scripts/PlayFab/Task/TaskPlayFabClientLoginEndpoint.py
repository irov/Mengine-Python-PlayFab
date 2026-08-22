from Foundation.TaskManager import TaskManager
import PlayFab.PlayFabErrors as PlayFabErrors
import PlayFab.PlayFabSettings as PlayFabSettings

from PlayFab.Task.TaskPlayFabHTTPEndpoint import TaskPlayFabHTTPEndpoint


class TaskPlayFabClientLoginEndpoint(TaskPlayFabHTTPEndpoint):
    Skiped = True
    UpdateEntityToken = True

    @staticmethod
    def _scheduleAttribution(settings_for_user):
        disabled_ads = PlayFabSettings.DisableAdvertising
        advertising_id_type = PlayFabSettings.AdvertisingIdType
        advertising_id_value = PlayFabSettings.AdvertisingIdValue

        if (not settings_for_user or
                not settings_for_user["NeedsAttribution"] or
                disabled_ads or
                not advertising_id_type or
                not advertising_id_value):
            return

        request = {}

        if advertising_id_type == PlayFabSettings.AD_TYPE_IDFA:
            request["Idfa"] = advertising_id_value
        elif advertising_id_type == PlayFabSettings.AD_TYPE_ANDROID_ID:
            request["Adid"] = advertising_id_value

        request_chain = TaskManager.createTaskChain()

        with request_chain as source:
            source.addTask(
                "TaskPlayFabClientAttributeInstall",
                Request=request,
                Cb=lambda response, error: None)

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

        TaskPlayFabClientLoginEndpoint._scheduleAttribution(response.get("SettingsForUser"))
