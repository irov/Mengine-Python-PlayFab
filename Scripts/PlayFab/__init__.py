def onInitialize():
    Trace.msg_dev("PlayFab.onInitialize")

    from Foundation.TaskManager import TaskManager

    tasks = [
        "TaskPlayFabAuthenticationGetEntityToken",
        "TaskPlayFabClientExecuteCloudScript",
        "TaskPlayFabClientGetAccountInfo",
        "TaskPlayFabClientGetLeaderboard",
        "TaskPlayFabClientGetTitleData",
        "TaskPlayFabClientLinkCustomID",
        "TaskPlayFabClientLinkGameCenterAccount",
        "TaskPlayFabClientLinkGooglePlayGamesServicesAccount",
        "TaskPlayFabClientLoginWithGameCenter",
        "TaskPlayFabClientLoginWithGooglePlayGamesServices",
        "TaskPlayFabClientLoginWithPlayFab",
        "TaskPlayFabClientRegisterPlayFabUser",
        "TaskPlayFabClientUpdateUserTitleDisplayName",
        "TaskPlayFabCreateMatchmakingTicket",
        "TaskPlayFabMultiplayerCancelMatchmakingTicket",
        "TaskPlayFabMultiplayerCreateMatchmakingTicket",
        "TaskPlayFabMultiplayerGetMatch",
        "TaskPlayFabMultiplayerGetMatchmakingTicket",
        "TaskPlayFabPlatformLogin",
        "TaskPlayFabRequest",
    ]

    TaskManager.importTasks("PlayFab.Task", tasks)

    from PlayFab.PlayFabManager import PlayFabManager
    Mengine.addGlobalModule("PlayFabManager", PlayFabManager)

    PlayFabManager.initializeIdentityLinking()

    from TraceManager import TraceManager
    TraceManager.addTrace("PlayFab")

    from Foundation.Notificator import Notificator

    identities = [
        "onStartMatchSearch",
        "onCancelMatchSearch",
    ]

    for identity in identities:
        Notificator.addIdentity(identity)

    from Foundation.AccountManager import AccountManager

    def accountSetuper(accountID, isGlobal):
        if isGlobal is True:
            return

        def _cbPlayFabIdChanged(account_id, value):
            Mengine.setTextAlias('', '$SettingsPlayerID', 'ID_Setting_PlayerID')
            Mengine.setTextAliasArguments('', '$SettingsPlayerID', value)

        Mengine.addCurrentAccountSetting("PlayFabId", u"0", _cbPlayFabIdChanged)
        Mengine.addCurrentAccountSetting("FirstLogin", u"True", None)  # is PlayFab user registered

        DisplayName = PlayFabManager.getDefaultDisplayName()
        Mengine.addCurrentAccountSetting("DisplayName", unicode(DisplayName), None)

        Mengine.addCurrentAccountSetting("Password", u"12345678", None)
        Mengine.addCurrentAccountSetting("PlayFabCustomId", unicode(Mengine.generateUniqueIdentity(64)), None)

    AccountManager.addCreateAccountExtra(accountSetuper)

    EntityTypes = [
    ]

    from Foundation.Bootstrapper import Bootstrapper
    if Bootstrapper.loadEntities("PlayFab", EntityTypes) is False:
        return False

    return True


def onFinalize():
    Trace.msg_dev("PlayFab.onFinalize")

    from PlayFab.PlayFabManager import PlayFabManager
    PlayFabManager.finalizeIdentityLinking()
