import sys
def handleFatal(log,error):
    log.fatal(error)
    sys.exit()

def handleSkippable(log, error):
    log.fatal(error)
    sys.exit()