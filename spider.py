import select
import serial
import sys
import time
import threading

dev = "/dev/ttyUSB0"
baud_rate = 115200
timeout = 1

DEBUG=True
data_sync = threading.Semaphore(0)

class FileNode:

    def __init__(self, path, parent):

        self.path = path
        self.children = []
        self.parent = parent

    def append(self, node):
        self.children.append(node)

class Listener(threading.Thread):
    def __init__(self, c, t):

	threading.Thread.__init__(self)
        self.port = c
        self.running = True
        self.t = t
        self.output = ""
        self.w_ready = False

    def stop(self):
        self.running = False

    def clear(self):
        self.output = ""

    def run(self):

        while self.running:
            rset,wset,xset = select.select([self.port], [],[], self.t)
            for s in rset:
                if s == self.port:
                    data = c.read(0x100)
                    self.output += data
            if (not rset) and self.w_ready:
                data_sync.release()
                self.w_ready = False

    def display(msg):
        print msg

    def errdisplay(msg):
        if DEBUG:
            print msg

def parse_filename(f):
    #print "parse_filename: " + f.split(' ')[-1]
    return f.split(' ')[-1].strip('\n').strip('\r')

def is_valid_file(f):
    ret = True
    if f == '.':
        ret = False
    return ret
        
def execute(cmd, node):
    sys.stdout.flush()
    c.write(cmd + '\n')
    s.w_ready = True
    data_sync.acquire()
    #print "output: "
    #print s.output
    for f in s.output.split('\n'):
        if cmd not in f: # cmd will be echo'd out from target
            fname = parse_filename(f)
            if not is_valid_file(fname):
                continue
            elif "No such file or directory" in f:
                continue
            elif '#' in f:
                continue

            print "***** node.path: " + node.path
            child = FileNode(fname, node)
            node.append(child)

            newcmd = "ls -ld " + child.path + '*/'
            s.clear()
            execute(newcmd, child)


c = serial.Serial(dev, baud_rate, timeout=1)
s = Listener(c, timeout)
s.start()

root = FileNode('/', None)
cmd = raw_input("")
cmd = "ls -ld /*/"
execute(cmd, root)
data_sync.release()
s.stop()
