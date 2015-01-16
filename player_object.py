class PlayerObject(object):
    socket = None
    model_id = None
    point = 0
    answered = False

    def __init__(self, model, socket):
        self.socket = socket
        self.model_id = model_id
        self.point = 0
        self.answered = False