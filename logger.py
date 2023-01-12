class Logger():
    def __init__(self, proccess):
        self.proc=proccess

    def name(self, proccess):
        self.proc=proccess

    def info(self,message):
        print(f"({self.proc}) [INFO]: ", message)

    def fatal(self,message):
        print(f"({self.proc}) [FATAL]: ", message)

    def warn(self,message):
        print(f"({self.proc}) [WARN]: ", message)