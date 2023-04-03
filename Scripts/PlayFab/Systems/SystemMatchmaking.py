# coding=utf-8
from Foundation.System import System
from Foundation.TaskManager import TaskManager

from PlayFab.PlayFabManager import PlayFabManager


QUEUE_1_VS_1_NAME = "queue_dots_1vs1"
GIVE_UP_AFTER_SECONDS = 100


class SystemMatchmaking(System):

    def __init__(self):
        super(SystemMatchmaking, self).__init__()
        self.tickets = {}
        self.matches = {}
        self.match_id = None

    def _onRun(self):
        self.addObserver(Notificator.onStartMatchSearch, self.__cbStartMatchSearch)
        self.addObserver(Notificator.onCancelMatchSearch, self.__cbCancelMatchSearch)

        return True

    def __cbStartMatchSearch(self, semaphore):
        with TaskManager.createTaskChain(name="MatchSearch") as tc:
            with tc.addRaceTask(2) as (tc_matchmaking, tc_cancel):
                tc_matchmaking.addScope(self.__scopeCreateTicket)
                tc_matchmaking.addScope(self.__scopeCheckTicketStatus)
                tc_matchmaking.addScope(self.__scopeGetMatch)
                tc_matchmaking.addSemaphore(semaphore, To=True)

                tc_cancel.addListener(Notificator.onCancelMatchSearch)

        return False

    def __scopeCreateTicket(self, source):
        semaphore_ticket_created = Semaphore(False, "TicketCreated")

        def success_cb(ticket_id):
            # print "SystemMatchmaking success_cb args", ticket_id
            self.tickets[QUEUE_1_VS_1_NAME] = ticket_id
            semaphore_ticket_created.setValue(True)

        def fail_cb(*args):
            print("SystemMatchmaking fail_cb args", args)

        source.addScope(
            PlayFabManager.scopeCreateMatchmakingTicket,    # fixme
            GIVE_UP_AFTER_SECONDS,
            QUEUE_1_VS_1_NAME,
            success_cb,
            fail_cb
        )
        source.addSemaphore(semaphore_ticket_created, From=True)

    def __scopeCheckTicketStatus(self, source):
        def success_cb(response):
            # print "SystemMatchmaking success_cb args", response
            if response["Status"] == "Matched":
                # print "MATCHED"
                self.matches[QUEUE_1_VS_1_NAME] = response["MatchId"]
                semaphore_match_is_ready.setValue(True)

        def fail_cb(*args):
            print("SystemMatchmaking fail_cb args", args[0].GenerateErrorReport())
            pass

        semaphore_match_is_ready = Semaphore(False, "MatchIsReady")
        ticket_id = self.tickets.get(QUEUE_1_VS_1_NAME)
        if ticket_id is None:
            Trace.log("System", 0, "ticket_id is None")
            return

        with source.addRepeatTask() as (source_repeat, source_until):
            source_repeat.addScope(
                PlayFabManager.scopeGetMatchmakingTicket,    # fixme
                ticket_id,
                QUEUE_1_VS_1_NAME,
                success_cb,
                fail_cb
            )
            source_repeat.addDelay(6000)

            source_until.addSemaphore(semaphore_match_is_ready, From=True)

    def __scopeGetMatch(self, source):
        match_id = self.matches.get(QUEUE_1_VS_1_NAME)
        if match_id is None:
            Trace.log("System", 0, "match_id is None")
            return

        def success_cb(response):
            # print "SystemMatchmaking success_cb args", response
            pass

        def fail_cb(*args):
            print("SystemMatchmaking fail_cb args", args[0].GenerateErrorReport())
            pass

        source.addScope(
            PlayFabManager.scopeGetMatch,    # fixme
            match_id,
            QUEUE_1_VS_1_NAME,
            success_cb,
            fail_cb
        )

    def __cbCancelMatchSearch(self):
        ticket_id = self.tickets.get(QUEUE_1_VS_1_NAME)
        if ticket_id is None:
            return

        def internal_success_cb(response):
            del self.tickets[QUEUE_1_VS_1_NAME]

        def internal_fail_cb(response):
            pass

        PlayFabManager.callCancelMatchmakingTicket(    # fixme
            ticket_id=ticket_id,
            queue_name=QUEUE_1_VS_1_NAME,
            success_cb=internal_success_cb,
            fail_cb=internal_fail_cb
        )
        return False
