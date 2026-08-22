from Foundation.Task.TaskHeaderData import TaskHeaderData


class TaskPlayFabRequest(TaskHeaderData):
    Skiped = True

    def _onFastSkip(self):
        return True

    def _onSkip(self):
        request_id = self.id
        self.id = None

        if request_id is None or request_id == 0:
            return

        Mengine.cancelRequest(request_id)
