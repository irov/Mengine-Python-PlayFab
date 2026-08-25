import PlayFab.PlayFabErrors as PlayFabErrors
import PlayFab.PlayFabSettings as PlayFabSettings

from PlayFab.Task.TaskPlayFabAuthenticationGetEntityToken import TaskPlayFabAuthenticationGetEntityToken


class TaskPlayFabAuthenticationGetEntityTokenForce(TaskPlayFabAuthenticationGetEntityToken):
    CompleteOnCancel = True

    def _getAuthorization(self):
        session_ticket = PlayFabSettings._internalSettings.ClientSessionTicket

        if not session_ticket:
            raise PlayFabErrors.PlayFabException("Must be logged in to refresh the EntityToken")

        return "X-Authorization", session_ticket
