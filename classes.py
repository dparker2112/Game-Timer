class LedRGB:
    def __init__(self):
        self.state = 0
        self.r = 100
        self.g = 100
        self.b = 100
        self.update = 0

    def setR(self, setPoint):
        self.r = setPoint
        self.update = 1

    def setG(self, setPoint):
        self.g = setPoint
        self.update = 1

    def setB(self, setPoint):
        self.b = setPoint
        self.update = 1

    def setState(self, state):
        self.state = state
        self.update = 1