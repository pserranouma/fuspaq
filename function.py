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
