class Logger():
    def __init__(self, proccess, pad=20):
        self.proc=proccess
        self.pad=max(pad-len(proccess),0)

    def name(self, proccess):
        self.proc=proccess

    def info(self,message):
        print(f"({self.proc})"+" "*self.pad+"[INFO]: ", message)

    def fatal(self,message):
        print(f"({self.proc})"+" "*self.pad+"[FATAL]: ", message)

    def warn(self,message):
        print(f"({self.proc})"+" "*self.pad+"[WARN]: ", message)