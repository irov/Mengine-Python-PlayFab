import PlayFab.PlayFabClientAPI as PlayFabClientAPI

from PlayFabBaseMethods import PlayFabBaseMethods


class PlayFabClientManager(PlayFabBaseMethods):
    @staticmethod
    def prepareRegisterPlayFabUser(user, password, success_cb, fail_cb, **error_handlers):
        @PlayFabClientManager.do_before_cb(success_cb)
        def __success_cb(response):
            Mengine.changeCurrentAccountSetting("Name", unicode(user))
            Mengine.changeCurrentAccountSetting("Password", unicode(password))
            return response

        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.RegisterPlayFabUser,
            {
                "Username": user,
                # "DisplayName": user,
                "Password": password,
                "RequireBothUsernameAndEmail": False
            },
            __success_cb, fail_cb,
            [
                "AccountNotFound",
                "InvalidEmailOrPassword",
                "InvalidTitleId",
                "RequestViewConstraintParamsNotAllowed",
            ],
            error_handlers)

    @staticmethod
    def callRegisterPlayFabUser(user, password, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareRegisterPlayFabUser,
            user, password,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeRegisterPlayFabUser(source, user, password, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareRegisterPlayFabUser,
            user, password,
            success_cb, fail_cb, **error_handlers)

    # LoginWithPlayFab
    @staticmethod
    def prepareLoginWithPlayFab(user, password, success_cb, fail_cb, **error_handlers):
        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.LoginWithPlayFab,
            {
                "Username": user,
                "Password": password,
                "TitleId": "1"
            },
            success_cb, fail_cb, [
                "AccountNotFound",
                "InvalidTitleId",
                "InvalidUsernameOrPassword",
                "RequestViewConstraintParamsNotAllowed",
            ],
            error_handlers)

    @staticmethod
    def prepareLoginWithAndroidDeviceID(device_id, success_cb, fail_cb, **error_handlers):
        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.LoginWithAndroidDeviceID,
            {
                "AndroidDeviceId": str(device_id),
                "CreateAccount": False
            },
            success_cb, fail_cb, [
                "EncryptionKeyMissing",
                "EvaluationModePlayerCountExceeded",
                "InvalidSignature",
                "InvalidSignatureTime",
                "PlayerSecretAlreadyConfigured",
                "PlayerSecretNotConfigured",
                "RequestViewConstraintParamsNotAllowed",
            ],
            error_handlers)

    @staticmethod
    def prepareLinkAndroidDeviceID(device_id, force_link, success_cb, fail_cb, **error_handlers):
        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.LinkAndroidDeviceID,
            {
                "AndroidDeviceId": str(device_id),
                "ForceLink": force_link,
            },
            success_cb, fail_cb, [
                "LinkedDeviceAlreadyClaimed",
            ],
            error_handlers)

    @staticmethod
    def prepareUnLinkAndroidDeviceID(device_id, success_cb, fail_cb, **error_handlers):
        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.UnlinkAndroidDeviceID,
            {
                "AndroidDeviceId": str(device_id),
            },
            success_cb, fail_cb, [
                "AccountNotLinked",
                "DeviceNotLinked"
            ],
            error_handlers)

    @staticmethod
    def callLoginWithPlayFab(user, password, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareLoginWithPlayFab,
            user, password,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginWithPlayFab(source, user, password, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareLoginWithPlayFab,
            user, password,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginWithAndroidDeviceID(source, device_id, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareLoginWithAndroidDeviceID,
            device_id,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLinkAndroidDeviceID(source, device_id, force_link, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareLinkAndroidDeviceID,
            device_id, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeUnLinkAndroidDeviceID(source, device_id, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareUnLinkAndroidDeviceID,
            device_id,
            success_cb, fail_cb, **error_handlers)

    # UpdateUserTitleDisplayName
    @staticmethod
    def prepareUpdateUserTitleDisplayName(new_name, success_cb, fail_cb, **error_handlers):
        @PlayFabClientManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("DisplayName", {})
            return Data

        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.UpdateUserTitleDisplayName,
            {
                "DisplayName": new_name
            },
            __success_cb, fail_cb, [
                "InvalidPartnerResponse",
                "NameNotAvailable",
                "ProfaneDisplayName",
                "UsernameNotAvailable",
            ],
            error_handlers)

    @staticmethod
    def callUpdateUserTitleDisplayName(new_name, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareUpdateUserTitleDisplayName,
            new_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeUpdateUserTitleDisplayName(source, new_name, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareUpdateUserTitleDisplayName,
            new_name,
            success_cb, fail_cb, **error_handlers)

    # GetUserReadOnlyData
    @staticmethod
    def prepareGetUserReadOnlyData(list_of_keys, success_cb, fail_cb, **error_handlers):
        @PlayFabClientManager.do_before_cb(success_cb)
        def __success_cb(response):
            data = response.get("Data", {})
            return data

        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.GetUserReadOnlyData,
            {
                "Keys": list_of_keys
            },
            __success_cb, fail_cb,
            [
                # no possible error codes in playfab documentation
            ],
            error_handlers)

    @staticmethod
    def callGetUserReadOnlyData(list_of_keys, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareGetUserReadOnlyData,
            list_of_keys,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetUserReadOnlyData(source, list_of_keys, success_cb, fail_cb, **error_handlers):
        source.addScope(PlayFabClientManager.scopePlayFabAPI,
                        PlayFabClientManager.prepareGetUserReadOnlyData,
                        list_of_keys,
                        success_cb, fail_cb, **error_handlers)

    # GetTitleData
    @staticmethod
    def prepareGetTitleData(list_of_keys, success_cb, fail_cb, **error_handlers):
        @PlayFabClientManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("Data", {})
            return Data

        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.GetTitleData,
            {
                "Keys": list_of_keys
            },
            __success_cb, fail_cb,
            [
                # no possible error codes in playfab documentation
            ],
            error_handlers)

    @staticmethod
    def callGetTitleData(list_of_keys, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareGetTitleData,
            list_of_keys,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetTitleData(source, list_of_keys, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareGetTitleData,
            list_of_keys,
            success_cb, fail_cb, **error_handlers)

    # GetLeaderboard
    @staticmethod
    def prepareGetLeaderboard(statistic_name, max_result_count, profile_constraints,
                              success_cb, fail_cb, **error_handlers):
        @PlayFabClientManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("Leaderboard", {})
            return Data

        if not profile_constraints:
            profile_constraints = {}

        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.GetLeaderboard,
            {
                "StartPosition": 0,
                "StatisticName": statistic_name,
                "MaxResultsCount": max_result_count,
                "ProfileConstraints": profile_constraints
            },
            __success_cb, fail_cb,
            [
                "LeaderboardVersionNotAvailable"
            ],
            error_handlers)

    @staticmethod
    def callGetLeaderboard(statistic_name, max_result_count, profile_constraints,
                           success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareGetLeaderboard,
            statistic_name, max_result_count, profile_constraints,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetLeaderboard(source, statistic_name, max_result_count, profile_constraints,
                            success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareGetLeaderboard,
            statistic_name, max_result_count, profile_constraints,
            success_cb, fail_cb, **error_handlers)

    # GetLeaderboardAroundPlayer
    @staticmethod
    def prepareGetLeaderboardAroundPlayer(statistic_name, max_result_count, profile_constraints,
                                          success_cb, fail_cb, **error_handlers):
        @PlayFabClientManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("Leaderboard", {})
            return Data

        if not profile_constraints:
            profile_constraints = {}

        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.GetLeaderboardAroundPlayer,
            {
                "StatisticName": statistic_name,
                "MaxResultsCount": max_result_count,
                "ProfileConstraints": profile_constraints
            },
            __success_cb, fail_cb,
            [
                "AccountNotFound",
                "LeaderboardVersionNotAvailable"
            ],
            error_handlers)

    @staticmethod
    def callGetLeaderboardAroundPlayer(statistic_name, max_result_count, profile_constraints,
                                       success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareGetLeaderboardAroundPlayer,
            statistic_name, max_result_count, profile_constraints,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetLeaderboardAroundPlayer(source, statistic_name, max_result_count, profile_constraints,
                                        success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareGetLeaderboardAroundPlayer,
            statistic_name, max_result_count, profile_constraints,
            success_cb, fail_cb, **error_handlers)

    # GetAccountInfo
    @staticmethod
    def prepareGetAccountInfo(success_cb, fail_cb, **error_handlers):
        @PlayFabClientManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("AccountInfo", {})
            return Data

        playfab_id = Mengine.getCurrentAccountSetting("PlayFabId")

        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.GetAccountInfo,
            {
                "PlayFabId": playfab_id
            },
            __success_cb, fail_cb,
            [
                "AccountNotFound"
            ],
            error_handlers)

    @staticmethod
    def callGetAccountInfo(success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareGetAccountInfo,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetAccountInfo(source, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareGetAccountInfo,
            success_cb, fail_cb, **error_handlers)

    # GetPlayerStatistics
    @staticmethod
    def prepareGetPlayerStatistics(statistic_names, success_cb, fail_cb, **error_handlers):
        @PlayFabClientManager.do_before_cb(success_cb)
        def __success_cb(response):
            Data = response.get("Statistics", {})
            return Data

        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.GetPlayerStatistics,
            {
                "StatisticNames": statistic_names
            },
            __success_cb, fail_cb,
            [
                # no possible error codes in playfab documentation
            ],
            error_handlers)

    @staticmethod
    def callGetPlayerStatistics(statistic_names, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareGetPlayerStatistics,
            statistic_names,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetPlayerStatistics(source, statistic_names, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareGetPlayerStatistics,
            statistic_names,
            success_cb, fail_cb, **error_handlers)

    # UpdatePlayerStatistics
    @staticmethod
    def prepareUpdatePlayerStatistics(statistics, success_cb, fail_cb, **error_handlers):
        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.UpdatePlayerStatistics,
            {
                "Statistics": statistics
            },
            success_cb, fail_cb,
            [
                "AccountNotFound",
                "APINotEnabledForGameClientAccess",
                "DuplicateStatisticName",
                "StatisticCountLimitExceeded",
                "StatisticNameConflict",
                "StatisticNotFound",
                "StatisticValueAggregationOverflow",
                "StatisticVersionClosedForWrites",
                "StatisticVersionInvalid",
            ],
            error_handlers)

    @staticmethod
    def callUpdatePlayerStatistics(statistics, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareUpdatePlayerStatistics,
            statistics,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeUpdatePlayerStatistics(source, statistics, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareUpdatePlayerStatistics,
            statistics,
            success_cb, fail_cb, **error_handlers)

    # UpdateAvatarUrl
    @staticmethod
    def prepareUpdateAvatarUrl(image_url, success_cb, fail_cb, **error_handlers):
        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.UpdateAvatarUrl,
            {
                "ImageUrl": image_url
            },
            success_cb, fail_cb,
            [
                # no possible error codes in pl__on_get_profile_picture_linkayfab documentation
            ],
            error_handlers)

    @staticmethod
    def callUpdateAvatarUrl(image_url, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareUpdateAvatarUrl,
            image_url,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeUpdateAvatarUrl(source, image_url, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareUpdateAvatarUrl,
            image_url,
            success_cb, fail_cb, **error_handlers)

    # LinkFacebookAccount
    @staticmethod
    def prepareLinkFacebookAccount(access_token, force_link, success_cb, fail_cb, **error_handlers):
        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.LinkFacebookAccount,
            {
                "AccessToken": access_token,  # facebook access token
                "ForceLink": force_link  # boolean
            },
            success_cb, fail_cb,
            [
                "AccountAlreadyLinked",
                "FacebookAPIError",
                "InvalidFacebookToken",
                "LinkedAccountAlreadyClaimed",
            ],
            error_handlers)

    # LoginFacebookAccount
    @staticmethod
    def prepareLoginFacebookAccount(access_token, create_account, success_cb, fail_cb, **error_handlers):
        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.LoginWithFacebook,
            {
                "AccessToken": access_token,  # facebook access token
                "CreateAccount": create_account,
                # Automatically create a PlayFab account if one is not currently linked to this ID.
            },
            success_cb, fail_cb,
            [
                "EncryptionKeyMissing",
                "EvaluationModePlayerCountExceeded",
                "FacebookAPIError",
                "InvalidFacebookToken",
                "PlayerSecretAlreadyConfigured",
                "PlayerSecretNotConfigured",
                "RequestViewConstraintParamsNotAllowed",
            ],
            error_handlers)

    @staticmethod
    def callLinkFacebookAccount(access_token, force_link, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareLinkFacebookAccount,
            access_token, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLinkFacebookAccount(source, access_token, force_link, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareLinkFacebookAccount,
            access_token, force_link,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeLoginFacebookAccount(source, access_token, create_account, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareLoginFacebookAccount,
            access_token, create_account,
            success_cb, fail_cb, **error_handlers)

    # ExecuteCloudScript
    @staticmethod
    def prepareExecuteCloudScript(function_name, params, success_cb, fail_cb, **error_handlers):
        # print "[PlayFabClientManager|ExecuteCloudScript] CALL '{}' with params={}".format(function_name, params)

        revision = DefaultManager.getDefault("DefaultRevisionSelection", "Live")

        @PlayFabClientManager.do_before_cb(success_cb)
        def __success_cb(response):
            # print " ^-- [PlayFabClientManager|ExecuteCloudScript] SUCCESS '{}' --^\n".format(function_name)

            function_result = response.get("FunctionResult")
            return function_result

        return PlayFabClientManager.preparePlayFabAPI(
            PlayFabClientAPI.ExecuteCloudScript,
            {
                "FunctionName": function_name,
                "FunctionParameter": params,
                "RevisionSelection": revision,
            },
            __success_cb, fail_cb,
            [
                "CloudScriptAPIRequestCountExceeded",
                "CloudScriptAPIRequestError",
                "CloudScriptFunctionArgumentSizeExceeded",
                "CloudScriptHTTPRequestError",
                "CloudScriptNotFound",
                "JavascriptException",
            ],
            error_handlers)

    @staticmethod
    def callExecuteCloudScript(function_name, params, success_cb, fail_cb, **error_handlers):
        PlayFabClientManager.callPlayFabAPI(
            PlayFabClientManager.prepareExecuteCloudScript,
            function_name, params,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeExecuteCloudScript(source, function_name, params, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabClientManager.scopePlayFabAPI,
            PlayFabClientManager.prepareExecuteCloudScript,
            function_name, params,
            success_cb, fail_cb, **error_handlers)
