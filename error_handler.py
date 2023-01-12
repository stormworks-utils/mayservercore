import sys
def handleFatal(log,error):
    log.fatal(error)
    sys.exit()