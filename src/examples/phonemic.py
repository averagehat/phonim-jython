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
from logging import error, info, debug

#open shell for debugging purposes
def open_shell(l):
    import code
    # do something here
    vars = globals()
    vars.update(l)
    shell = code.InteractiveConsole(vars)
    shell.interact()


def get_speech():
    """Return None when run by python or phonemic.jar cannot be found."""
    try:
        import java
    except ImportError:
        return None

    try:
        jar_path = sys.argv[-1:] if len(sys.argv) > 1 else ['lib/phonemic.jar']
        print jar_path
#        jar_path = sys.argv[-1:] or '../../lib/phonemic.jar'
        #sys.path.extend(sys.argv[-1:])
        sys.path.extend(jar_path)
        import org.sodbeans.phonemic.TextToSpeechFactory as TextToSpeechFactory
    except java.lang.UnsatisfiedLinkError:
        pass
    except ImportError, err:
        print >> sys.stderr, 'cannot find phonemic.jar: %s' % str(err)
        return None
    else:
        speech = TextToSpeechFactory.getDefaultTextToSpeech()
        return speech
    sys.exit(1)

class Phonemic(object):
    def __init__(self, nbsock):
        self.nbsock = nbsock
        self.speech = get_speech()
        self.last_col, self.last_lnum = -1, -1

    def _speak(self, text):
        if self.speech:
            self.speech.speakBlocking(text)
        else:
            # Print on stdout when phonemic is not available.
            sys.stdout.write('speak> "' + text + '"' + os.linesep)

    def speak_admin_msg(self, text):
        self._speak(text)

    def get_cursor_change(self, buf):
        if buf.col < 1 or buf.lnum < 1:
            raise ValueError('Either buffer column ', buf.col, 'buf.lnum ', buf.lnum, ' was illegal value (less than one)')
        if self.last_col == -1: #this is the first dx/dy event
            self.last_col, self.last_lnum = 1, 1
        new_col, new_lnum = buf.col, buf.lnum
        dx, dy =  buf.col - self.last_col, buf.lnum - self.last_lnum
        self.last_col, self.last_lnum = buf.col, buf.lnum
        return dx, dy

        #is cusor movement in insert mode already handled as a netbeans event?
    def speak_change(self, buf):
        dx, dy = self.get_cursor_change(buf)
        if dy:
             self._speak_line(buf)
        elif dx:
             self._speak_column_change(buf)
        else:
             pass
    # the cursor didn't move
    def parse_msg(self, raw_msg): 
        return PMessage(raw_msg)

    #-----------------------------------------------------------------------
    #   Events
    #-----------------------------------------------------------------------

    def event_startupDone(self):
        self.speak_admin_msg('Phonemic is connected to Vim.')

    def event_disconnect(self):
        self.speak_admin_msg('Phonemic is disconnected from Vim.')

    def event_fileOpened(self, buf):
        if not buf:
            self.speak_admin_msg(
                    'You cannot use netbeans on a "[No Name]" file.\n'
                    'Please, edit a file.'
                    )
            return

        # Set this buffer as "owned" by Netbeans so as to get buttonRelease
        # events.
        self.nbsock.send_cmd(buf, u'netbeansBuffer', u'T')
        self.speak_admin_msg('Opening the file %s.' % buf.get_basename())

    def event_killed(self, buf):
        self.speak_admin_msg('Closing the file %s.' % buf.get_basename())

    def event_version(self, version):
        self.speak_admin_msg('Vim netbeans version is %s.' % version)

    def event_balloonText(self, text):
        self.speak_admin_msg(text)

    def event_buttonRelease(self, buf, button):
        self.speak_admin_msg('Button %d at line %d and column %d.'
                                            % (button, buf.lnum, buf.col))

    # it seems like this will be called alongside keyAtPos?
    # it gets called alongside default_cmd_processing?
    def event_keyCommand(self, buf, keyName):
        #open_shell(locals())
        print 'in phonemic.keyCommand '
        self.speak_admin_msg(keyName)

    def event_newDotAndMark(self, buf):
        self.speak_admin_msg('Cursor offset at %d.' % buf.offset)

    def event_insert(self, buf, text):
        self.speak_admin_msg('The following text was inserted'
                                ' at byte offset %d: %s.' % (buf.offset, text))

    def event_remove(self, buf, length):
        self.speak_admin_msg('%d bytes of text were removed at byte offset %d.'
                                                        % (length, buf.offset))

    def event_save(self, buf):
        self.speak_admin_msg('Buffer %s has been saved.' % buf.get_basename())

    def event_tick(self):
        pass

    #-----------------------------------------------------------------------
    #   Commands
    #-----------------------------------------------------------------------

    def default_cmd_processing(self, buf, cmd, args):
        """Handle nbkey commands not matched with a 'cmd_<keyName>' method."""
        info('nbkey: %s', (cmd, args, buf))

    def cmd_speak(self, buf, args):
        self._speak(args)

    def cmd_length(self, buf, args):
        """Get the length of the buffer."""
        class LengthObserver(object):
            def update(self, observable, length):
                speak('The length of buffer %s is %s'
                                % (buf.get_basename(), length))

        speak = self.speak
        self.nbsock.send_function(buf, u'getLength', LengthObserver())

    def cmd_quit(self, buf, args):
        self._quit()

    def _quit(self):
        """Terminate the server."""
        self.nbsock.terminate_server()
