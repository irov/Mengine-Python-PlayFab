from Foundation.DefaultManager import DefaultManager
from Foundation.Manager import Manager
from PlayFab.PlayFabClientManager import PlayFabClientManager
from PlayFab.PlayFabMultiplayerManager import PlayFabMultiplayerManager

class PlayFabManager(Manager, PlayFabClientManager, PlayFabMultiplayerManager):
    s_debug_pretty_print = None

    @staticmethod
    def _onInitialize(*args):
        PlayFabManager.s_debug_pretty_print = DefaultManager.getDefaultBool("DebugDataPrettyPrint", False)