def onInitialize():
    from Foundation.EntityManager import EntityManager
    from Foundation.ObjectManager import ObjectManager

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

    Types = [

    ]

    if Mengine.getGameParamBool("NotUseDefaultEntitiesList", False) is True:
        Types = []
        from Foundation.DatabaseManager import DatabaseManager
        records = DatabaseManager.getDatabaseRecordsFilterBy("Database", "Entities", Module="PlayFabManager")

        for record in records:
            Types.append(record.get("Type"))

    ObjectManager.importObjects("Game.Objects", Types)
    EntityManager.importEntities("Game.Entities", Types)

    from Foundation.AccountManager import AccountManager

    def accountSetuper(accountID, isGlobal):
        if isGlobal is True:
            return

        def _cbPlayFabIdChanged(account_id, value):
            Mengine.setTextAlias('', '$SettingsPlayerID', 'ID_Setting_PlayerID')
            Mengine.setTextAliasArguments('', '$SettingsPlayerID', value)

        Mengine.addCurrentAccountSetting("PlayFabId", u"0", _cbPlayFabIdChanged)
        Mengine.addCurrentAccountSetting("FirstLogin", u"True", None)  # is PlayFab user registered

        Mengine.addCurrentAccountSetting("DisplayName", u"You", None)
        PlayFabManager.setDefaultDisplayName()

        Mengine.addCurrentAccountSetting("Password", u"12345678", None)

    AccountManager.addCreateAccountExtra(accountSetuper)

    return True


def onFinalize():
    pass
