#!/usr/bin/python

import sys
sys.path.append('/usr/local/lib/python2.7/dist-packages')

import os
import threading
import wave
import getopt
from time import sleep
import datetime
from random import randint
import signal

import pjsua as pj

lib = None
current_call = None
global_lock = None
with_media = False
is_running = True

def receive_signal(signo, frame):
    global is_running
    is_running = False

def log_cb(level, str, len):
    print str,

class MyAccountCallback(pj.AccountCallback):
    sem = None

    def __init__(self, account=None):
        pj.AccountCallback.__init__(self, account)

    def wait(self):
        self.sem = threading.Semaphore(0)
        self.sem.acquire()

    def on_reg_state(self):
        if self.sem:
            if self.account.info().reg_status >= 200:
                self.sem.release()

    def on_incoming_call(self, call):
        global current_call
        if current_call:
            call.answer(486, 'Busy')
            return
        current_call = call
        call_cb = MyCallCallback(current_call)
        current_call.set_callback(call_cb)
        current_call.answer(180)


class MyCallCallback(pj.CallCallback):

    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)
        print ('MyCallCallback.__init__(call=', call, ')')

    def on_state(self):
        global current_call
        global global_lock
        global in_call
        global lib
        print 'Call with', self.call.info().remote_uri,
        print 'is', self.call.info().state_text,
        print 'last code =', self.call.info().last_code,
        print '(' + self.call.info().last_reason + ')',
        print 'CALL_INFO [callid => ', self.call.info().sip_call_id,
        print 'media_state => ', self.call.info().media_state,
        print 'role => ', self.call.info().role

        if self.call.info().state == pj.CallState.DISCONNECTED:
            print 'Call state DISCONNECTED. call = ', current_call, 'thread_id = ', threading.current_thread().ident, 'name = ', threading.current_thread().name
            current_call = None

            in_call = False
            if global_lock:
                print "Releasing global_lock()"
                log_flush()
                global_lock.release()
                print "global_lock() released"
                log_flush()

        elif self.call.info().state == pj.CallState.CALLING:
            print 'Call State => CALLING'
            in_call = True

        elif self.call.info().state == pj.CallState.INCOMING:
            print 'Call State => INCOMING'
            in_call = True

        elif self.call.info().state == pj.CallState.EARLY:
            print 'Call state => EARLY '
            in_call = True

        elif self.call.info().state == pj.CallState.CONNECTING:
            print 'Call State => CONNECTING'
            in_call = True

        elif self.call.info().state == pj.CallState.CONFIRMED:
             print 'Call state CONFIRMED'
             in_call = True
             if with_media:
                 wfile = wave.open('long.wav')
                 time = 1.0 * wfile.getnframes() / wfile.getframerate()
                 wfile.close()
                 call_slot = self.call.info().conf_slot
                 self.wav_player_id = lib.create_player('long.wav', loop=False)
                 self.wav_slot = lib.player_get_slot(self.wav_player_id)
                 lib.conf_connect(self.wav_slot, call_slot)
             else:
                 print "No MEDIA mode"
        return

    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            print 'Media is now active'
        else:
            print 'Media is inactive: ', self.call.info().media_state


def usage(prog):
    print """Usage: %s options
          options:
              -l [login],       --login=[login]
              -p [password],    --password=[password]
              -d [domain],      --domain=[domain]
              -P [proxy],       --proxy=[proxy]
              -D [destination], --destination=[num]    <= optional
              -m                --media                <= optional
              -h                --help                 <= optional
              -v                --verbose              <= optional
          """ % (prog)

def log_flush():
    sys.stdout.flush()
    sys.stderr.flush()

def terminate_app(code):
    global lib
    if lib:
        lib.destroy()
        lib = None

    sys.exit(code)
    return

def make_call(uri):
    try:
        cb = MyCallCallback()
        print 'Making call to', uri
        print ('Setting callback to: ', cb)
        return acc.make_call(uri, cb)
    except pj.Error as e:
        print 'Exception: ' + str(e)
        return

    return


def cb_func(pid):
    print '%s playback is done' % pid
    current_call.hangup()


try:
    login = None
    password = None
    domain = None
    proxy = None
    destination = None
    caller_mode = None
    verbose = False
    proto = "TCP"

    signal.signal(signal.SIGHUP,  receive_signal)
    signal.signal(signal.SIGINT,  receive_signal)
    signal.signal(signal.SIGTERM, receive_signal)

    try:
        opts, args = getopt.getopt(sys.argv[1:],"l:p:d:P:D:mhv",["login=","password=","domain=","proxy=","destination=","media","help","verbose","tls","tcp","udp"])
    except getopt.GetoptError:
        usage(sys.argv[0])
        terminate_app(2)

    for opt,arg in opts:
        if opt in ("-h", "--help"):
            usage(sys.argv[0])
            terminate_app(0)
        elif opt in ("-l", "--login"):
            login = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-d", "--domain"):
            domain = arg
        elif opt in ("-P", "--proxy"):
            proxy = arg
        elif opt in ("-D", "--destination"):
            destination = arg
            caller_mode = True
        elif opt in ("--tls"):
            proto = "TLS"
        elif opt in ("--tcp"):
            proto = "TCP"
        elif opt in ("--udp"):
            proto = "UDP"
        elif opt in ("-m", "--media"):
            with_media = True
        elif opt in ("-v", "--verbose"):
            verbose = True
        else:
            print "Unknown option: ", opt
            usage(sys.argv[0])
            terminate_app(2)
    if not login or not password or not domain or not proxy:
        usage(sys.argv[0])
        terminate_app(2)

    if caller_mode:
        print "Started in CALLER mode"
    else:
        print "Started in CALLEE mode"

    lib = pj.Lib()


    my_ua_cfg = pj.UAConfig()
    my_ua_cfg.nameserver = ['8.8.8.8', '8.8.4.4']
    my_ua_cfg.user_agent = 'pjSIP Python'
    my_ua_cfg.max_calls = 10

    my_media_cfg = pj.MediaConfig()
    my_media_cfg.no_vad = True
    my_media_cfg.enable_ice = False
    my_media_cfg.enable_turn = False

    if verbose:
        lib.init(ua_cfg=my_ua_cfg, media_cfg=my_media_cfg, log_cfg=pj.LogConfig(level=5, callback=log_cb))
    else:
        lib.init(ua_cfg=my_ua_cfg, media_cfg=my_media_cfg, log_cfg=pj.LogConfig(level=0, callback=log_cb))

    if proto == "TLS":
        transport = lib.create_transport(pj.TransportType.TLS, pj.TransportConfig())
    elif proto == "TCP":
        transport = lib.create_transport(pj.TransportType.TCP, pj.TransportConfig())
    else:
        transport = lib.create_transport(pj.TransportType.UDP, pj.TransportConfig())

    lib.set_null_snd_dev()
    lib.start()
    lib.handle_events()

    acc_cfg = pj.AccountConfig()

    print 'sipclient.py -- Simple SIP Client use PJSUA Python Module (PJSIP API)'
    print ''
    print 'Registration:'
    succeed = 0
    while succeed == 0:
        acc_cfg.id = 'sip:' + login + '@' + domain
        print 'SIP URL is: ', acc_cfg.id

        acc_cfg.reg_uri = 'sip:' + domain
        print 'URL of the registrar', acc_cfg.reg_uri

        acc_cfg.proxy = []
        proxy_tmp = 'sip:' + proxy

        if proto == "TLS":
            proxy_tmp += ';transport=tls;lr'
        elif proto == "TCP":
            proxy_tmp += ';transport=tcp;lr'
        else:
            proxy_tmp += ';transport=udp;lr'

        print ('URL of the proxy [', proxy_tmp, ']')
        acc_cfg.proxy.append(proxy_tmp)

        realm = domain
        username = login
        passwd = password

        acc_cfg.auth_cred = [pj.AuthCred(realm, username, passwd)]
        acc_cb = MyAccountCallback()
        acc = lib.create_account(acc_cfg, cb=acc_cb)
        acc_cb.wait()
        if str(acc.info().reg_status) == '200' or str(acc.info().reg_status) == '403':
            succeed = 1
        else:
            print ''
            print 'Registration failed, status=', acc.info().reg_status,
            print '(' + acc.info().reg_reason + ')'
            print ''
            print 'Please try again !'

    print ''
    print 'Registration complete, status=', acc.info().reg_status,
    print '(' + acc.info().reg_reason + ')'

    my_sip_uri = acc_cfg.id + ':' + str(transport.info().port)
    in_call = None
    #global_lock = threading.Semaphore(0)
    while True:
        log_flush()

        if not is_running:
            break

        if caller_mode:
            print "Caller mode"
            sleep(1)
            dst_num = destination
            registrar = acc_cfg.reg_uri.split(':')
            dst_uri = 'sip:' + dst_num + '@' + registrar[1]
            if not in_call:
                call_start_time = datetime.datetime.now()
                print 'Making a call: ', current_call
                lck = lib.auto_lock()
                in_call = True
                current_call = make_call(dst_uri)
                del lck
                sleep(2)
            else:
                current = datetime.datetime.now()
                duration = current - call_start_time
                if duration.seconds > randint(20, 40):
                    print duration.seconds, ' seconds passed, hanging up'
                    lck = lib.auto_lock()
                    current_call.hangup()
                    in_call = False
                    if global_lock:
                        print "locking global_lock()"
                        global_lock.acquire()
                        print "passed global_lock()"
                    del lck
                    sleep(5) # Wait a bit before making a new call

                    print 'HANGUP finished. thread_id = ', threading.current_thread().ident, 'thread_name = ', threading.current_thread().name
        else:
            print "Callee mode"
            sleep(1)

            if not in_call:
                pass
            elif current_call:
                lck = lib.auto_lock()
                if current_call:
                    state = current_call.info().state
                del lck

                if state == pj.CallState.EARLY:
                    call_start_time = datetime.datetime.now()
                    lck = lib.auto_lock()
                    current_call.answer(200)
                    del lck
                    print "Answering a call. thread_id = ', threading.current_thread().ident, 'thread_name = ', threading.current_thread().name"
	        elif state == pj.CallState.CONFIRMED:
                    current = datetime.datetime.now()
                    duration = current - call_start_time
                    if duration.seconds > randint(20, 40):
                        print duration.seconds, ' seconds passed, terminating long call'
                        lck = lib.auto_lock()
                        print "Calling .hangup()"
                        current_call.hangup()
                        print "Finished .hangup()"
                        in_call = False
                        if global_lock:
                            print "locking global_lock()"
                            log_flush()
                            global_lock.acquire()
                            print "global_lock() passed"
                            log_flush()
                        del lck
                        print 'HANGUP finished. thread_id = ', threading.current_thread().ident, 'thread_name = ', threading.current_thread().name

    if in_call:
        print "Main loop exited"
        lck = lib.auto_lock()
        current_call.hangup()
        in_call=False
        del lck

    print "Terminating"
    log_flush()
    sleep(2)

    lib.destroy()
    lib = None
    transport = None
    acc_cb = None
except pj.Error as e:
    print 'Exception: ' + str(e)
    terminate_app(1)
