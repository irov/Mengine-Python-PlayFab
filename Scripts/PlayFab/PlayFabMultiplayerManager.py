# coding=utf-8
from PlayFab.PlayFabBaseMethods import PlayFabBaseMethods


class PlayFabMultiplayerManager(PlayFabBaseMethods):
    @staticmethod
    def prepareCreateMatchmakingTicket(title_player_id, give_up_after_second, queue_name,
                                       success_cb, fail_cb, **error_handlers):
        @PlayFabMultiplayerManager.do_before_cb(success_cb)
        def __success_cb(response):
            """ Повинно повернути TicketId який потім використовуємо для запиту інформацію
            про білет методом getMatchmakingTicket

            :param response: dict, повинен містити TicketId
            :return: TicketId
            """
            return response.get("TicketId")

        return PlayFabMultiplayerManager.preparePlayFabEndpoint(
            "TaskPlayFabMultiplayerCreateMatchmakingTicket",
            {
                "Creator": {
                    "Entity": {
                        "Id": title_player_id,
                        "Type": "title_player_account"
                    }
                },
                "GiveUpAfterSeconds": give_up_after_second,
                "QueueName": queue_name,

            },
            __success_cb, fail_cb,
            [
                "MatchmakingAttributeInvalid",
                "MatchmakingBadRequest",
                "MatchmakingEntityInvalid",
                "MatchmakingMemberProfileInvalid",
                "MatchmakingNumberOfPlayersInTicketTooLarge",
                "MatchmakingPlayerAttributesInvalid",
                "MatchmakingPlayerAttributesTooLarge",
                "MatchmakingQueueNotFound",
                "MatchmakingRateLimitExceeded",
                "MatchmakingTicketMembershipLimitExceeded",
                "MatchmakingUnauthorized",
            ],
            error_handlers)

    @staticmethod
    def callCreateMatchmakingTicket(title_player_id, give_up_after_second, queue_name,
                                    success_cb, fail_cb, **error_handlers):
        return PlayFabMultiplayerManager.callPlayFabEndpoint(
            PlayFabMultiplayerManager.prepareCreateMatchmakingTicket,
            title_player_id, give_up_after_second, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeCreateMatchmakingTicket(source, give_up_after_second, queue_name, success_cb, fail_cb, **error_handlers):
        source.addTask(
            "TaskPlayFabCreateMatchmakingTicket",
            GiveUpAfterSecond=give_up_after_second,
            QueueName=queue_name,
            SuccessCb=success_cb,
            FailCb=fail_cb,
            ErrorHandlers=error_handlers)

    @staticmethod
    def prepareGetMatchmakingTicket(ticket_id, queue_name, success_cb, fail_cb, **error_handlers):
        """ Запит статусу по створеному білеті

        Запитуємо кожні 6с щоб отримати статус білету, коли статус == Matched, то беремо MatchId і викликаємо getMatch

        :param ticket_id:
        :param queue_name:
        :param success_cb:
        :param fail_cb:
        :param error_handlers:
        :return:
        """

        @PlayFabMultiplayerManager.do_before_cb(success_cb)
        def __success_cb(response):
            """
            Основне що нам потрібне з response - MatchId який потім використовуємо в запиті getMatch
            і Status == Matched, то можемо починати гру
            якщо статус
            :param response: dict
                CancellationReasonString - The reason why the current ticket was canceled.
                    his field is only set if the ticket is in canceled state.
                Created	- The server date and time at which ticket was created.
                Creator	- The Creator's entity key.
                GiveUpAfterSeconds - How long to attempt matching this ticket in seconds.
                MatchId	- The Id of a match.
                Members	- A list of Users that have joined this ticket.
                MembersToMatchWith - A list of PlayFab Ids of Users to match with.
                QueueName - The Id of a match queue.
                Status - The current ticket status. Possible values are: WaitingForPlayers, WaitingForMatch,
                    WaitingForServer, Canceled and Matched.
                TicketId - The Id of the ticket to find a match for.
            :return: response
            """
            return response

        return PlayFabMultiplayerManager.preparePlayFabEndpoint(
            "TaskPlayFabMultiplayerGetMatchmakingTicket",
            {
                "TicketId": ticket_id,
                "QueueName": queue_name,
                "EscapeObject": False,
            },
            __success_cb, fail_cb,
            [
                "MatchmakingEntityInvalid",
                "MatchmakingQueueNotFound",
                "MatchmakingRateLimitExceeded",
                "MatchmakingRequestTypeMismatch",
                "MatchmakingTicketNotFound",
                "MatchmakingUnauthorized",
            ],
            error_handlers)

    @staticmethod
    def callGetMatchmakingTicket(ticket_id, queue_name, success_cb, fail_cb, **error_handlers):
        return PlayFabMultiplayerManager.callPlayFabEndpoint(
            PlayFabMultiplayerManager.prepareGetMatchmakingTicket,
            ticket_id, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetMatchmakingTicket(source, ticket_id, queue_name, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabMultiplayerManager.scopePlayFabEndpoint,
            PlayFabMultiplayerManager.prepareGetMatchmakingTicket,
            ticket_id, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def prepareGetMatch(match_id, queue_name, success_cb, fail_cb, **error_handlers):
        @PlayFabMultiplayerManager.do_before_cb(success_cb)
        def __success_cb(response):
            """

            :param response: dict
                MatchId	- The Id of a match.
                Members	- A list of Users that are matched together, along with their team assignments.
                RegionPreferences - A list of regions that the match could be played in sorted by preference.
                    This value is only set if the queue has a region selection rule.
                ServerDetails - The details of the server that the match has been allocated to.
            :return:
            """

            return response

        return PlayFabMultiplayerManager.preparePlayFabEndpoint(
            "TaskPlayFabMultiplayerGetMatch",
            {
                "MatchId": match_id,
                "QueueName": queue_name,
                "EscapeObject": False,
                "ReturnMemberAttributes": False,
            },
            __success_cb, fail_cb,
            [
                "MatchmakingEntityInvalid",
                "MatchmakingMatchNotFound",
                "MatchmakingQueueNotFound",
                "MatchmakingRateLimitExceeded",
                "MatchmakingUnauthorized",
            ],
            error_handlers)

    @staticmethod
    def callGetMatch(match_id, queue_name, success_cb, fail_cb, **error_handlers):
        return PlayFabMultiplayerManager.callPlayFabEndpoint(
            PlayFabMultiplayerManager.prepareGetMatch,
            match_id, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetMatch(source, match_id, queue_name, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabMultiplayerManager.scopePlayFabEndpoint,
            PlayFabMultiplayerManager.prepareGetMatch,
            match_id, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def prepareCancelMatchmakingTicket(ticket_id, queue_name, success_cb, fail_cb, **error_handlers):
        @PlayFabMultiplayerManager.do_before_cb(success_cb)
        def __success_cb(response):
            return response

        return PlayFabMultiplayerManager.preparePlayFabEndpoint(
            "TaskPlayFabMultiplayerCancelMatchmakingTicket",
            {
                "TicketId": ticket_id,
                "QueueName": queue_name,
            },
            __success_cb, fail_cb,
            [
                "MatchmakingEntityInvalid",
                "MatchmakingPlayerHasNotJoinedTicket",
                "MatchmakingQueueNotFound",
                "MatchmakingTicketAlreadyCompleted",
                "MatchmakingTicketNotFound",
                "MatchmakingUnauthorized",
            ],
            error_handlers)

    @staticmethod
    def callCancelMatchmakingTicket(ticket_id, queue_name, success_cb, fail_cb, **error_handlers):
        return PlayFabMultiplayerManager.callPlayFabEndpoint(
            PlayFabMultiplayerManager.prepareCancelMatchmakingTicket,
            ticket_id, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeCancelMatchmakingTicket(source, ticket_id, queue_name, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabMultiplayerManager.scopePlayFabEndpoint,
            PlayFabMultiplayerManager.prepareCancelMatchmakingTicket,
            ticket_id, queue_name,
            success_cb, fail_cb, **error_handlers)
