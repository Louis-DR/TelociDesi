import time

class Log:
    current_depth = 0
    VERBOSE = True
    MIN_DEPTH = 0
    MAX_DEPTH = 2
    def __init__(self, action="doing an unnamed action"):
        self.action = action
        self.depth = Log.current_depth
        Log.current_depth +=1
        self.startTime = 0
        self.start()
    
    def start(self):
        if Log.VERBOSE and self.depth in range(Log.MIN_DEPTH, Log.MAX_DEPTH):
            print('  '*self.depth+"Starting "+self.action+"...")
        self.startTime = time.time()
    
    def stop(self):
        t_timeElapsed = 1000*(time.time()-self.startTime)
        if Log.VERBOSE and self.depth in range(Log.MIN_DEPTH, Log.MAX_DEPTH):
            print("{:<100} {:>10}".format('  '*self.depth+"Done "+self.action+"..." , "{:.2f} ms".format(t_timeElapsed)))
        Log.current_depth -=1



# log = Log("measuring")
# for k in range(5000):
#     logm = Log("iteration number {}".format(k))
#     logm.stop()
# log.stop()