from PlayFab.PlayFabClientManager import PlayFabClientManager
from PlayFab.PlayFabMultiplayerManager import PlayFabMultiplayerManager

from Foundation.Manager import Manager
from Foundation.DefaultManager import DefaultManager

class PlayFabManager(Manager, PlayFabClientManager, PlayFabMultiplayerManager):
    s_debug_pretty_print = None

    @staticmethod
    def _onInitialize(*args):
        PlayFabManager.s_debug_pretty_print = DefaultManager.getDefaultBool("DebugDataPrettyPrint", False)
