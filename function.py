class function:
    def __init__(self, name, servicename, params={}):
        self.servicename = servicename
        if len(params) == 0:
            self.name = name
        else:
            l = list(params.items())
            pname = ''
            for i in range(len(l)):
                pname = pname + str(l[i][0]) + str(l[i][1])
            self.name = name + pname
        self.params = params
        self.execTime = 0
        self.cost = 0
        self.ux = 0
        # energy management:
        self.energy = 0
        self.consData = []
        self.consDataLast = 0
        self.consDataStart = 0
        self.consDataTotal = -1
        self.startTime = 0
        self.replicas = 1