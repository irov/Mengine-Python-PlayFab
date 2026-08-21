# coding=utf-8
import PlayFab.PlayFabAuthenticationAPI as PlayFabAuthenticationAPI
import PlayFab.PlayFabMultiplayerAPI as PlayFabMultiplayerAPI
import PlayFab.PlayFabSettings as PlayFabSettings

from PlayFab.PlayFabBaseMethods import PlayFabBaseMethods
from PlayFab.PlayFabErrors import PlayFabError


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

        return PlayFabMultiplayerManager.preparePlayFabAPI(
            PlayFabMultiplayerAPI.CreateMatchmakingTicket,
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
        return PlayFabMultiplayerManager.callPlayFabAPI(
            PlayFabMultiplayerManager.prepareCreateMatchmakingTicket,
            title_player_id, give_up_after_second, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeCreateMatchmakingTicket(source, give_up_after_second, queue_name, success_cb, fail_cb, **error_handlers):
        def __task_cb(isSkip, __complete_cb):
            completed = [False]

            def __complete_once(cb, value):
                if completed[0] is True:
                    return

                completed[0] = True

                try:
                    cb(value)
                finally:
                    __complete_cb(isSkip)

            def __success_cb(response):
                __complete_once(success_cb, response)

            def __fail_cb(error):
                if isinstance(error, PlayFabError) is False:
                    error = PlayFabError(error)

                __complete_once(fail_cb, error)

            def __entity_token_cb(response, error):
                if error is not None:
                    __fail_cb(error)
                    return

                entity = response.get("Entity") if isinstance(response, dict) else None
                title_player_id = entity.get("Id") if isinstance(entity, dict) else None

                if title_player_id is None:
                    __fail_cb(PlayFabError({
                        "code": 400,
                        "status": "Invalid Entity Token",
                        "error": "InvalidParams",
                        "errorCode": 1000,
                        "errorMessage": "PlayFab entity token response has no entity id",
                    }))
                    return

                started = PlayFabMultiplayerManager.callCreateMatchmakingTicket(
                    title_player_id, give_up_after_second, queue_name,
                    __success_cb, __fail_cb, **error_handlers)

                if started is False and completed[0] is False:
                    __fail_cb(PlayFabError())

            if isSkip is True:
                __complete_cb(isSkip)
                return

            try:
                PlayFabAuthenticationAPI.GetEntityToken({}, __entity_token_cb)
            except Exception as e:
                PlayFabSettings.GlobalExceptionLogger(e)
                __fail_cb(PlayFabError())

        source.addCallback(__task_cb)

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

        return PlayFabMultiplayerManager.preparePlayFabAPI(
            PlayFabMultiplayerAPI.GetMatchmakingTicket,
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
        return PlayFabMultiplayerManager.callPlayFabAPI(
            PlayFabMultiplayerManager.prepareGetMatchmakingTicket,
            ticket_id, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetMatchmakingTicket(source, ticket_id, queue_name, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabMultiplayerManager.scopePlayFabAPI,
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

        return PlayFabMultiplayerManager.preparePlayFabAPI(
            PlayFabMultiplayerAPI.GetMatch,
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
        return PlayFabMultiplayerManager.callPlayFabAPI(
            PlayFabMultiplayerManager.prepareGetMatch,
            match_id, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeGetMatch(source, match_id, queue_name, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabMultiplayerManager.scopePlayFabAPI,
            PlayFabMultiplayerManager.prepareGetMatch,
            match_id, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def prepareCancelMatchmakingTicket(ticket_id, queue_name, success_cb, fail_cb, **error_handlers):
        @PlayFabMultiplayerManager.do_before_cb(success_cb)
        def __success_cb(response):
            return response

        return PlayFabMultiplayerManager.preparePlayFabAPI(
            PlayFabMultiplayerAPI.CancelMatchmakingTicket,
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
        return PlayFabMultiplayerManager.callPlayFabAPI(
            PlayFabMultiplayerManager.prepareCancelMatchmakingTicket,
            ticket_id, queue_name,
            success_cb, fail_cb, **error_handlers)

    @staticmethod
    def scopeCancelMatchmakingTicket(source, ticket_id, queue_name, success_cb, fail_cb, **error_handlers):
        source.addScope(
            PlayFabMultiplayerManager.scopePlayFabAPI,
            PlayFabMultiplayerManager.prepareCancelMatchmakingTicket,
            ticket_id, queue_name,
            success_cb, fail_cb, **error_handlers)
