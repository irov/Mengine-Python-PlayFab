def onInitialize():
    from PlayFab.PlayFabManager import PlayFabManager
    Mengine.addGlobalModule("PlayFabManager", PlayFabManager)

    from TraceManager import TraceManager
    TraceManager.addTrace("PlayFab")

    from Foundation.Notificator import Notificator

    identities = [
        "onStartMatchSearch",
        "onCancelMatchSearch",
    ]

    for identity in identities:
        Notificator.addIdentity(identity)

    EntityTypes = [
    ]

    from Foundation.Bootstrapper import Bootstrapper
    if Bootstrapper.loadEntities("Game", EntityTypes) is False:
        return False

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

    AccountManager.addCreateAccountExtra(accountSetuper)

    return True


def onFinalize():
    pass
