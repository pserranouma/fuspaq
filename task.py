class task:

    def __init__(self, name):
        self.name = name
        self.description = ""
        self.services = []

    def addService(self, service):
        self.services.append(service)

    def getService(self, name):
        for s in self.services:
            if s.name == name:
                return s
        return None