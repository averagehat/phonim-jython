#! /usr/bin/env python
# Copyright 2011 Xavier de Gaye
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import time
import re
import optparse
import threading
import asyncore
import asynchat
import socket
import Queue
import cStringIO
import logging
import ConfigParser
from logging import error, info, debug

VERSION=0.3 # no spaces
SECTION_NAME = 'vimoir properties'
BUFFER_SIZE = 4096
DEFAULTS = {
    'vimoir.netbeans.python.client': 'src.examples.phonemic.Phonemic',
    'vimoir.netbeans.host': '',
    'vimoir.netbeans.port': '3219',
    'vimoir.netbeans.password': 'changeme',
    'vimoir.netbeans.encoding': 'UTF-8',
    'vimoir.netbeans.timeout': '20',
    'vimoir.netbeans.user_interval': '200',
}
RE_ESCAPE = ur'["\n\t\r\\]'                                             \
            ur'# RE: escaped characters in a string'
RE_UNESCAPE = ur'\\["ntr\\]'                                            \
              ur'# RE: escaped characters in a quoted string'
RE_AUTH = ur'^\s*AUTH\s*(?P<passwd>\S+)\s*$'                            \
          ur'# RE: password authentication'
RE_RESPONSE = ur'^\s*(?P<seqno>\d+)\s*(?P<args>.*)\s*$'                 \
              ur'# RE: a netbeans response'
RE_EVENT = ur'^\s*(?P<buf_id>\d+):(?P<event>\S+)=(?P<seqno>\d+)'        \
           ur'\s*(?P<args>.*)\s*$'                                      \
           ur'# RE: a netbeans event message'
RE_LNUMCOL = ur'^(?P<lnum>\d+)/(?P<col>\d+)'                            \
             ur'# RE: lnum/col'
RE_TOKEN_SPLIT = r'\s*"((?:\\"|[^"])+)"\s*|\s*([^ "]+)\s*'              \
                 r'# RE: split a string in tokens, handling quotes'

# compile regexps
re_escape = re.compile(RE_ESCAPE, re.VERBOSE)
re_unescape = re.compile(RE_UNESCAPE, re.VERBOSE)
re_auth = re.compile(RE_AUTH, re.VERBOSE)
re_response = re.compile(RE_RESPONSE, re.VERBOSE)
re_event = re.compile(RE_EVENT, re.VERBOSE)
re_lnumcol = re.compile(RE_LNUMCOL, re.VERBOSE)
re_token_split = re.compile(RE_TOKEN_SPLIT, re.VERBOSE)

def escape_char(matchobj):
    """Escape special characters in string."""
    if matchobj.group(0) == u'"': return ur'\"'
    if matchobj.group(0) == u'\n': return ur'\n'
    if matchobj.group(0) == u'\t': return ur'\t'
    if matchobj.group(0) == u'\r': return ur'\r'
    if matchobj.group(0) == u'\\': return ur'\\'
    assert False

def unescape_char(matchobj):
    """Remove escape on special characters in quoted string."""
    if matchobj.group(0) == ur'\"': return u'"'
    if matchobj.group(0) == ur'\n': return u'\n'
    if matchobj.group(0) == ur'\t': return u'\t'
    if matchobj.group(0) == ur'\r': return u'\r'
    if matchobj.group(0) == ur'\\': return u'\\'
    assert False

def unquote(msg):
    """Remove escapes from escaped characters in a quoted string."""
    return u'%s' % re_unescape.sub(unescape_char, msg)

def evt_ignore(buf_id, msg, arg_list):
    """Ignore not implemented received events."""
    pass

def setup_logger(debug):
    """Setup the logger."""
    fmt = logging.Formatter('%(levelname)-7s %(message)s')
    stderr_hdlr = StderrHandler()
    stderr_hdlr.setFormatter(fmt)
    root = logging.getLogger()
    root.addHandler(stderr_hdlr)
    level = logging.ERROR
    if debug:
        level = logging.DEBUG
    root.setLevel(level)

def load_properties(filename):
    """Load configuration properties."""
    opts = RawConfigParser(DEFAULTS)
    try:
        f = FileLike(filename)
        opts.readfp(f)
        f.close()
        info('loading properties from %s', filename)
    except IOError, e:
        error('cannot load properties, using defaults: %s', e)
        opts.add_section(SECTION_NAME)
    except ConfigParser.ParsingError, e:
        error(e)
    return opts

def check_bufID(evt_method):
    """Decorator to check the bufID in a Netbeans event methods."""
    def _decorator(self, parsed):
        buf = self._bset.getbuf_at(parsed.buf_id)
        assert buf is not None, ('invalid bufId "%d" at %s'
                                % (parsed.buf_id, evt_method.func_name))
        return evt_method(self, parsed)
    return _decorator

class NetbeansException(Exception):
    """The base class of all Netbeans exceptions."""

class NetbeansInvalidPathnameException(NetbeansException):
    """This exception is raised when a buffer pathname is invalid."""

class RawConfigParser(ConfigParser.RawConfigParser):
    """A RawConfigParser subclass with a getter and no section parameter."""
    def get(self, option):
        return ConfigParser.RawConfigParser.get(self, SECTION_NAME, option)

class FileLike(object):
    """File like object to read a java properties file with RawConfigParser."""
    def __init__(self, fname):
        self.name = fname
        self.f = None

    def readline(self):
        if not self.f:
            self.f = open(self.name)
            return '[%s]\n' % SECTION_NAME
        return self.f.readline()

    def close(self):
        if self.f:
            self.f.close()

class StderrHandler(logging.StreamHandler):
    """Stderr logging handler."""

    def __init__(self):
        self.strbuf = cStringIO.StringIO()
        self.doflush = True
        logging.StreamHandler.__init__(self, self.strbuf)

    def should_flush(self, doflush):
        """Set flush mode."""
        self.doflush = doflush

    def write(self, string):
        """Write to the StringIO buffer."""
        self.strbuf.write(string)

    def flush(self):
        """Flush to stderr when enabled."""
        if self.doflush:
            value = self.strbuf.getvalue()
            if value:
                print >> sys.stderr, value,
                self.strbuf.truncate(0)

    def close(self):
        """Close the handler."""
        self.flush()
        self.strbuf.close()
        logging.StreamHandler.close(self)

class NetbeansFunction(object):
    """An Observable."""

    def __init__(self, seqno, observer):
        self.seqno = seqno
        self.observer = observer

class NetbeansClient(object):
    """This class implements all the NetbeansEventHandler methods.

    This class exists so as to be subclassed by implementations that want to
    ignore most events and to implement only the ones they are interested in.
    """
    def __init__(self, nbsock):
        self.nbsock = nbsock

    #-----------------------------------------------------------------------
    #   Events
    #-----------------------------------------------------------------------

    def event_startupDone(self):
        """Terminate the server on startup to allow only one Netbeans session."""
        self.nbsock.terminate_server()

    def event_disconnect(self):
        pass

    def event_fileOpened(self, buf):
        pass

    def event_killed(self, buf):
        pass

    def event_version(self, version):
        pass

    def event_balloonText(self, text):
        pass

    def event_buttonRelease(self, buf, button):
        pass

    def event_keyCommand(self, buf, keyName):
        pass

    def event_newDotAndMark(self, buf):
        pass

    def event_insert(self, buf, text):
        pass

    def event_remove(self, buf, length):
        pass

    def event_save(self, buf):
        pass

    def event_tick(self):
        pass

    #-----------------------------------------------------------------------
    #   Commands
    #-----------------------------------------------------------------------

    def default_cmd_processing(self, buf, cmd, args):
        pass

class Server(asyncore.dispatcher):
    def __init__(self, host, port, props_file):
        asyncore.dispatcher.__init__(self)
        self.props_file = props_file
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind_listen(host, port)

    def bind_listen(self, host, port):
        self.set_reuse_addr()
        self.bind((host, int(port)))
        self.listen(1)
        info('listening on: %s', (host, port))

    def handle_accept(self):
        """Accept the connection from Vim."""
        conn, addr = self.socket.accept()
        # Get the class to instantiate.
        opts = load_properties(self.props_file)
        name = opts.get('vimoir.netbeans.python.client')
        idx = name.rfind('.')
        if idx == -1:
            stmt = "import %s as clazz" % name
        else:
            stmt = "from %s import %s as clazz" % (name[:idx], name[idx+1:])
        try:
            exec stmt
        except ImportError, e:
            error('importing client class: %s', e)
            conn.close()
            return

        nbsock = Netbeans(self, addr, opts)
        client = clazz(nbsock)
        nbsock.set_client(client)
        conn.setblocking(0)
        nbsock.set_socket(conn)
        nbsock.connected = True
        info('%s connected to %s', clazz.__name__, addr)

    def handle_tick(self):
        pass

class Netbeans(asynchat.async_chat):
    """A Netbeans instance exchanges netbeans messages on a socket.

    Instance attributes:
        server: Server
            the server that accepted the connection
        addr: str
            remote address
        opts: RawConfigParser
            vimoir properties
        client: implements NetbeansEventHandler
            client class
        ibuff: list
            list of strings received from netbeans
        ready: boolean
            startupDone event has been received
        output_queue: Queue
            output netbeans messages
        observer_fifo: Queue
            fifo containing observers (notify a function reply)
        _bset: buffer.BufferSet
            buffer list
        seqno: int
            netbeans sequence number
        last_seqno: int
            last reply sequence number

    """

    def __init__(self, server, addr, opts):
        asynchat.async_chat.__init__(self)
        self.server = server
        self.addr = '[remote=%s:%s]' % addr
        self.opts = opts
        self.client = None
        self.set_terminator(u'\n')
        self.ibuff = []
        self.ready = False
        self.output_queue = Queue.Queue(0)
        self.outbuf = ''
        self.observer_fifo = Queue.Queue(0)
        self._bset = BufferSet()
        self.seqno = 0
        self.last_seqno = 0
        self.encoding = opts.get('vimoir.netbeans.encoding')

    def __getattr__(self, attr):
        """Override buggy __getattr__ asyncore method."""
        try:
            retattr = getattr(self.socket, attr)
        except AttributeError:
            msg = ("%s instance has no attribute '%s'"
                                 %(self.__class__.__name__, attr))
            if not attr.startswith('evt_') and not attr.startswith('cmd_'):
                error(msg)
            raise AttributeError(msg)
        return retattr

    def set_client(self, client):
        self.client = client

    def terminate_server(self):
        """Terminate the server."""
        info("terminating the server")
        self.server.close()

    def close(self):
        if not self.connected:
            return
        self.connected = False
        self.ready = False
        asynchat.async_chat.close(self)

        info('%s disconnected', self.addr)
        if self.client:
            try:
                self.client.event_disconnect()
            except Exception, e:
                self.handle_error()

    def collect_incoming_data(self, data):
        self.ibuff.append(unicode(data, self.encoding))

    def found_terminator(self):
        """Process new line terminated netbeans message."""
        msg = u''.join(self.ibuff)
        self.ibuff = []
        debug('%s %s', self.addr, msg)

        if not self.connected:
            return
        if not self.ready:
            self.open_session(msg)
            return

        parsed = Parser(msg)
        if parsed.is_event:
            evt_handler = getattr(self, "evt_%s" % parsed.event, evt_ignore)
            try:
                evt_handler(parsed)
            except Exception, e:
                type, value, traceback = sys.exc_info()
                raise asyncore.ExitNow, e, traceback

        # A function reply: process the reply.
        else:
            # Vim may send multiple replies for one function request.
            if parsed.seqno == self.last_seqno:
                return
            self.last_seqno = parsed.seqno

            if self.observer_fifo.empty():
                raise asyncore.ExitNow(
                    'got a function reply with no matching function request')

            function = self.observer_fifo.get()
            if function.seqno != parsed.seqno:
                raise asyncore.ExitNow(
                    "no match: expected seqno '%s' / seqno in function reply '%s'",
                        (function.seqno, parsed.seqno))
            if parsed.nbstring:
                arg = [parsed.nbstring]
            else:
                arg = parsed.arg_list
            try:
                function.observer.update(function, arg)
            except Exception, e:
                self.handle_error()

    def open_session(self, msg):
        """Process initial netbeans messages."""
        # 'AUTH changeme'
        matchobj = re_auth.match(msg)
        if matchobj:
            password = matchobj.group(u'passwd')
            if password != self.opts.get('vimoir.netbeans.password'):
                try:
                    raise NetbeansException('invalid password: "%s"' % password)
                except NetbeansException, e:
                    self.handle_error()
            return

        # '0:version=0 "2.3"'
        # '0:startupDone=0'
        else:
            parsed = Parser(msg)
            if parsed.is_event:
                try:
                    if parsed.event == u"version":
                        self.client.event_version(parsed.nbstring)
                        return
                    elif parsed.event == u"startupDone":
                        self.ready = True
                        self.client.event_startupDone()
                        return
                except Exception, e:
                    self.handle_error()
                    return
        raise asyncore.ExitNow('received unexpected message: "%s"' % msg)

    def get_buffer(pathname):
        return self._bset.get(pathname)

    def writable (self):
        return (self.connected
                and (not self.output_queue.empty() or self.outbuf))

    def initiate_send (self):
        self.refill_buffer()
        if not self.outbuf:
            return
        try:
            n = self.send(self.outbuf[:BUFFER_SIZE])
            if n:
                self.outbuf = self.outbuf[n:]
        except socket.error:
            self.handle_error()

    def refill_buffer (self):
        while not self.output_queue.empty() and len(self.outbuf) < BUFFER_SIZE:
            text = self.output_queue.get()
            self.outbuf += text

    def log_info(self, message, type='info'):
        """Override log_info to use 'logging' and log all as errors."""
        error(message)

    #-----------------------------------------------------------------------
    #   Events
    #-----------------------------------------------------------------------
    def evt_balloonText(self, parsed):
        """Report the text under the mouse pointer."""
        try:
            self.client.event_balloonText(parsed.nbstring)
        except Exception, e:
            self.handle_error()

    @check_bufID
    def evt_buttonRelease(self, parsed):
        """Report which button was pressed and the cursor location."""
        assert len(parsed.arg_list) == 3, 'invalid format in buttonRelease event'
        buf = self._bset.getbuf_at(parsed.buf_id)
        button, buf.lnum, buf.col = (int(x) for x in parsed.arg_list)
        try:
            self.client.event_buttonRelease(buf, button)
        except Exception, e:
            self.handle_error()

    def evt_disconnect(self, parsed):
        """Process a disconnect netbeans event."""
        self.close()

    def evt_fileOpened(self, parsed):
        """A file was opened by the user."""
        pathname = parsed.nbstring
        buf = None
        if pathname:
            assert os.path.isabs(pathname), 'absolute pathname required'
            buf = self._bset.get(pathname)
            assert (buf.buf_id == parsed.buf_id or parsed.buf_id == 0,
                                        'got fileOpened with wrong bufId')
            if parsed.buf_id == 0:
                self.send_cmd(buf, u'putBufferNumber', self.quote(pathname))
        try:
            self.client.event_fileOpened(buf)
        except Exception, e:
            self.handle_error()

    @check_bufID
    def evt_insert(self, parsed):
        """Text 'text' has been inserted in Vim at byte position 'offset'."""
        assert len(parsed.arg_list) == 1, 'invalid format in insert event'
        buf = self._bset.getbuf_at(parsed.buf_id)
        buf.offset = int(parsed.arg_list[0])
        try:
            self.client.event_insert(buf, parsed.nbstring)
        except Exception, e:
            self.handle_error()

    @check_bufID
    def evt_keyCommand(self, parsed):
        """Report a special key being pressed with name 'keyName'."""
        buf = self._bset.getbuf_at(parsed.buf_id)
        try:
            self.client.event_keyCommand(buf, parsed.nbstring)
        except Exception, e:
            self.handle_error()

    @check_bufID
    def evt_keyAtPos(self, parsed):
        """Process a keyAtPos netbeans event."""
        buf = self._bset.getbuf_at(parsed.buf_id)
        assert len(parsed.arg_list) == 2, 'invalid arg in keyAtPos'
        if not parsed.nbstring:
            debug('empty string in keyAtPos')
            return

        matchobj = re_lnumcol.match(parsed.arg_list[1])
        assert matchobj, 'invalid lnum/col: %s' % parsed.arg_list[1]
        buf.lnum = int(matchobj.group(u'lnum'))
        buf.col = int(matchobj.group(u'col'))
        cmd, args = (lambda a=u'', b=u'':
                            (a, b))(*parsed.nbstring.split(None, 1))
        try:
            try:
                method = getattr(self.client, 'cmd_%s' % cmd)
            except AttributeError:
                self.client.default_cmd_processing(buf, cmd, args)
            else:
                method(buf, args)
        except Exception, e:
            self.handle_error()

    @check_bufID
    def evt_killed(self, parsed):
        """A file was deleted or wiped out by the user."""
        buf = self._bset.getbuf_at(parsed.buf_id)
        try:
            self.client.event_killed(buf)
        except Exception, e:
            self.handle_error()

    @check_bufID
    def evt_newDotAndMark(self, parsed):
        """Report the cursor position as a byte offset."""
        assert len(parsed.arg_list) == 2, 'invalid format in newDotAndMark event'
        buf = self._bset.getbuf_at(parsed.buf_id)
        buf.offset = int(parsed.arg_list[0])
        try:
            self.client.event_newDotAndMark(buf)
        except Exception, e:
            self.handle_error()

    @check_bufID
    def evt_remove(self, parsed):
        """'length' bytes of text were deleted in Vim at position 'offset'."""
        assert len(parsed.arg_list) == 2, 'invalid format in remove event'
        buf = self._bset.getbuf_at(parsed.buf_id)
        buf.offset = int(parsed.arg_list[0])
        length = int(parsed.arg_list[1])
        try:
            self.client.event_remove(buf, length)
        except Exception, e:
            self.handle_error()

    @check_bufID
    def evt_save(self, parsed):
        """The buffer has been saved and is now unmodified."""
        buf = self._bset.getbuf_at(parsed.buf_id)
        try:
            self.client.event_save(buf)
        except Exception, e:
            self.handle_error()

    def handle_tick(self):
        try:
            self.client.event_tick()
        except Exception, e:
            self.handle_error()

    #-----------------------------------------------------------------------
    #   Commands - Functions
    #-----------------------------------------------------------------------

    def send_cmd(self, buf, cmd, args=u''):
        """Send a command to Vim."""
        self.send_request(u'%d:%s!%d%s%s\n', buf, cmd, args)

    def send_function(self, buf, function, *args):
        """Send a function to Vim.

        Invoked as:
            send_function(buf, function, observer)
            send_function(buf, function, params, observer)
        """
        params = u''
        l = len(args)
        if l == 0 or l > 2:
            raise NetbeansException(
                        'invalid number of arguments in send_function')
        if l == 1:
            observer = args[0]
        else:
            params = args[0]
            observer = args[1]
        if not hasattr(observer, 'update'):
            raise NetbeansException(
                        'last argument of send_function is not an Observer')
        self.send_request(u'%d:%s/%d%s%s\n', buf, function, params)
        self.observer_fifo.put(NetbeansFunction(self.seqno, observer))

    def send_request(self, fmt, buf, request, args):
        """Send a netbeans function or command."""
        self.seqno += 1
        buf_id = 0
        space = u' '
        if isinstance(buf, NetbeansBuffer):
            buf_id = buf.buf_id
        if not args:
            space = u''
        msg = fmt % (buf_id, request, self.seqno, space, args)

        if self.ready:
            self.output_queue.put(msg.encode(self.encoding))
            debug('%s %s', self.addr, msg.strip(u'\n'))
        else:
            info('error in send_request: Netbeans session not ready')

    def quote(msg):
        """Quote 'msg' and escape special characters."""
        return u'"%s"' % re_escape.sub(escape_char, msg)
    quote = staticmethod(quote)

    def split_quoted_string(msg):
        """Return the list of whitespace separated tokens from 'msg', handling
        double quoted substrings as a token.

         The '\' escaping character of the special characters in quoted
        substrings are removed.

        >>> print split_quoted_string(r'"a c" b v "this \\"is\\" foobar argument" Y ')
        ['a c', 'b', 'v', 'this "is" foobar argument', 'Y']

        """
        match = re_token_split.findall(msg)
        return [unquote(x) or y for x, y in match]
    split_quoted_string = staticmethod(split_quoted_string)

class Parser(object):
    """Parse a received netbeans message.

    Instance attributes:
        is_event: boolean
            True: an event - False: a reply
        buf_id: int
            netbeans buffer number
        event: str
            event name
        seqno: int
            netbeans sequence number
        nbstring: str
            the netbeans string
        arg_list: list
            list of remaining args after the netbeans string

    """

    def __init__(self, msg):
        matchobj = re_event.match(msg)
        if matchobj:
            # an event
            bufid_name = matchobj.group(u'buf_id')
            self.event = matchobj.group(u'event')
        else:
            # a reply
            bufid_name = u'0'
            self.event = u''
            matchobj = re_response.match(msg)
        if not matchobj:
            raise asyncore.ExitNow('invalid netbeans message: "%s"' % msg)
        self.is_event = (matchobj.re is re_event)

        seqno = matchobj.group(u'seqno')
        args = matchobj.group(u'args').strip()
        self.buf_id = int(bufid_name)
        self.seqno = int(seqno)

        # The quoted string is last in an 'insert' event.
        if self.event == u'insert':
            if not args:
                raise asyncore.ExitNow('invalid netbeans message: "%s"' % msg)
            idx = args.find(u' ')
            if idx == -1:
                raise asyncore.ExitNow('invalid netbeans message: "%s"' % msg)
            self.arg_list = [args[:idx]]
            args = args[idx+1:]

        # a netbeans string
        self.nbstring = u''
        if args and args[0] == u"\"":
            end = args.rfind(u"\"")
            if end != -1 and end != 0:
                self.nbstring = args[1:end]
                # Do not unquote nbkey parameter twice since vim already parses
                # function parameters as strings (see :help expr-quote).
                if not (self.event == u'keyAtPos' or self.event == u'keyCommand'):
                    self.nbstring = unquote(self.nbstring)
            else:
                end = -1
        else:
            end = -1

        if self.event != u'insert':
            self.arg_list = args[end+1:].split()

class NetbeansBuffer(object):
    """A Vim buffer.

    A NetbeansBuffer is never directly instantiated by the application.

    Instance attributes:
        pathname: readonly property
            full pathname
        offset: int
            cursor position in the buffer as a byte offset
        lnum: int
            line number of the cursor (first line is one)
        col: int
            column number of the cursor (in bytes, zero based)
        buf_id: int
            netbeans buffer number, starting at one

    """

    def __init__(self, pathname, buf_id):
        """Constructor."""
        if not os.path.isabs(pathname):
            raise NetbeansInvalidPathnameException(
                '"pathname" is not an absolute path: %s' % pathname)
        self.__pathname = pathname
        self.offset = 0
        self.lnum = 1
        self.col = 0
        self.buf_id = buf_id

    def get_pathname(self):
        """NetbeansBuffer full path name."""
        return self.__pathname
    pathname = property(get_pathname, None, None, get_pathname.__doc__)

    def get_basename(self):
        """Return the basename of the buffer pathname."""
        return os.path.basename(self.pathname)

    def __str__(self):
        """Return the string representation of the buffer."""
        return '%s:%s/%s' % (self.get_basename(), self.lnum, self.col)

    __repr__ = __str__

class BufferSet(object):
    """A container for a list and map of buffers.

    Instance attributes:
        buf_map: dict
            a dictionary of {pathname: NetbeansBuffer instance}.
        buf_list: list
            the list of NetbeansBuffer instances indexed by netbeans 'bufID'

    A NetbeansBuffer instance is never removed from BufferSet.

    """

    def __init__(self):
        """Constructor."""
        self.buf_map = {}
        self.buf_list = []
        self.lock = threading.Lock()

    def getbuf_at(self, buf_id):
        """Return the buffer at idx in list."""
        self.lock.acquire()
        try:
            if buf_id <= 0 or buf_id > len(self.buf_list):
                return None
            return self.buf_list[buf_id - 1]
        finally:
            self.lock.release()

    def get(self, pathname):
        """Get NetbeansBuffer with pathname, instantiate one when not found.

        The pathname parameter must be an absolute path name.

        """
        self.lock.acquire()
        try:
            if pathname not in self.buf_map:
                # Netbeans buffer numbers start at one.
                buf = NetbeansBuffer(pathname, len(self.buf_list) + 1)
                self.buf_map[pathname] = buf
                self.buf_list.append(buf)
            return self.buf_map[pathname]
        finally:
            self.lock.release()

def main():
    formatter = optparse.IndentedHelpFormatter(max_help_position=30)
    parser = optparse.OptionParser(
                    version='%prog ' + str(VERSION),
                    usage='usage: python %prog [options] args...',
                    formatter=formatter)
    parser.add_option('-d', '--debug',
            action="store_true", default=False,
            help='enable printing debug information')
    parser.add_option('--conf', type='string', default='.',
            help=('path to vimoir.properties directory (default \'%default\')'))
    (options, sys.argv) = parser.parse_args(args=sys.argv)
    setup_logger(options.debug)
    props_file = os.path.join(options.conf, 'vimoir.properties')
    opts = load_properties(props_file)

    Server(opts.get('vimoir.netbeans.host'), opts.get('vimoir.netbeans.port'),
                                                                    props_file)
    timeout = int(opts.get('vimoir.netbeans.timeout')) / 1000.0
    user_interval = (int(opts.get('vimoir.netbeans.user_interval')) / 1000.0)
    last = time.time()
    while asyncore.socket_map:
        asyncore.poll(timeout=timeout)

        # Send the timer events.
        now = time.time()
        if (now - last >= user_interval):
            last = now
            for obj in asyncore.socket_map.values():
                obj.handle_tick()

    # Terminate all Phonemic threads by exiting.
    sys.exit(0)

if __name__ == "__main__":
    if sys.version_info >= (3, 0):
        sys.stderr.write("Python 3 is not supported.\n")
        sys.exit(1)

    main()

