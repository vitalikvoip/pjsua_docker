#!/usr/bin/python

import sys
import time
from multiprocessing import Process
from random import randint
import os
import signal
import datetime

accounts = []
callers = []
callees = []

domain = None
proxy = None
proto = "tcp"

def die(reason):
    print "Terminating test: ", reason
    sys.exit(1)

def receive_signal(signal_number, frame):
    print "Received signalno: ", signal_number
    print "Stopping callers..."
    for ua in callers:
        ua.terminate()
    print "Stopping callees..."
    for ua in callees:
        ua.terminate()

def test_dir(dir):
    try:
        os.stat(dir)
    except:
        os.mkdir(dir)

def log_redirect(username):
    logfile_path = "logs/" + username + "_log.txt"
    logfile_dir = os.path.dirname(logfile_path)
    test_dir(logfile_dir)

    logfile = open(logfile_path,"a+",buffering=0)
    logfile_fd = logfile.fileno()
    stdout_fd = sys.stdout.fileno()
    stderr_fd = sys.stderr.fileno()
    os.dup2(logfile_fd,stdout_fd)
    os.dup2(logfile_fd,stderr_fd)

def caller_instance(username,password,destination):
    print "Worker for account started => %s:%s@%s  --> %s" % (username,password,domain,destination)
    log_redirect(username)
    #time.sleep(randint(1,5))
    print "Started at: ", datetime.datetime.now()
    os.execl('ua.py', 'ua.py', '-l',username,'-p',password,'-d',domain,'-P',proxy,'-D',destination,'--' + proto)
    sys.exit(0)

def callee_instance(username,password):
    print "Worker for account started => %s:%s@%s" % (username,password,domain)
    log_redirect(username)
    #time.sleep(randint(1,5))
    print "Started at: ", datetime.datetime.now()
    os.execl('ua.py', 'ua.py','-l',username,'-p',password,'-d',domain,'-P',proxy,'--' + proto)
    sys.exit(0)

def parse_credentials(filename):
    global accounts

    try:
        fp = open(filename)
        line = fp.readline()
        cnt = 0
        while line:
            credentials = line.strip().split(" ")
            account = {}
            account['login'] = credentials[0]
            account['password'] = credentials[1]
            account['id'] = cnt
            accounts.append(account)
            line = fp.readline()
            cnt += 1
    finally:
        fp.close()

def main():
    global accounts
    global domain
    global proxy
    global proto

    signal.signal(signal.SIGHUP, receive_signal)
    signal.signal(signal.SIGINT, receive_signal)
    signal.signal(signal.SIGTERM, receive_signal)

    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print "Usage: ", sys.argv[0], " file.csv", "domain outbound_proxy [protocol]"
        die("wrong arguments")

    filename = sys.argv[1]
    domain = sys.argv[2]
    proxy = sys.argv[3]
    if len(sys.argv) == 5:
        proto = sys.argv[4]

    parse_credentials(filename)

    accounts_number = len(accounts)
    half = accounts_number / 2
    total = half * 2 # to use only even number of accounts

    for idx in range(half):
        print "Creating caller: my_idx => ", idx, " dst_idx => ", idx + half
        account = accounts[idx]
        destination = accounts[idx+half]
        caller = Process(target=caller_instance, args=(account['login'],account['password'],destination['login']))
        callers.append(caller)

    for idx in range(half,total):
        print "Creating callee: my_idx => ", idx
        account = accounts[idx]
        callee = Process(target=callee_instance, args=(account['login'],account['password']))
        callees.append(callee)

    for child in callers:
        print "Starting caller: ", child
        child.start()

    for child in callees:
        print "Starting callee: ", child
        child.start()

    for child in callers:
        child.join()
        print "Caller finished: ", child

    for child in callees:
        child.join()
        print "Callee finished: ", child

    print "Test has finished!"

if __name__ == "__main__":
    main()
