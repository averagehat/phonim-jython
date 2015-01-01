from phonemic import Phonemic
import re
import os
import sys
from logging import error, info, debug

NEWLINE_ENCODING = ' '
TEST = True
# Currently raising exceptions here causes netbeans-client to disconnect 
# and can be recoonected via :nbstart 
# this includes unintentional exceptions
# we need a nicer way to handle malformed vim requests

def open_shell(l):
    import code
    # do something here
    vars = globals()
    vars.update(l)
    shell = code.InteractiveConsole(vars)
    shell.interact()

class PhonimException(Exception):
  """Generic exception"""

class PhonimBadArgumentException(PhonimException):
  """Malformed args """

class PhonimNBKeyMessageInvalidArgsException(PhonimException):
  """The args passed to the :nbkey command were not properly formed."""

class PhonimCommandNotImplemented(PhonimException):
  """The command does not exist"""

class PhonimCommandNotExist(PhonimException):
  """This command is a valid phonemic command but it is not yet implemented"""

"""Defines the keyAtPos commands """
class Phonim(Phonemic):
    # because the text (one of the parameters)can have spaces in it.
    # allow floats, words ( no spaces ), ints
    PARAMS_REGEX = ur'([A-z]+)=([A-z\.0-9]+)' ur'(?:&(([A-z]+)=[A-z\.0-9])' \
       ur'|'  ur'(text=[.\s]+))*'
    params_re = re.compile(PARAMS_REGEX)

    def parse_args(nbkey_method):
      def _decorator(self, args):
        if not params_re.match(args):
          raise PhonimNBKeyMessageInvalidArgsException()
        # check that url params with regex
        params = urlparse.parse_qs(args)
        for k, v in params:
          params[k] = v[0]
      return _decorator
    
    def __init__(self, nbsock):
        self.nbsock = nbsock
        self.speech = self.get_speech()

    def get_speech(self):
        print 'kiddie, test:' , TEST
        if not TEST:
            super(Phonim, self).get_speech()
        else:
            jar_path = 'Users/wovenhead/phonim/current/src/test/test.jar'
            sys.path.append(jar_path)
            sys.path.append('lib/phonemic.jar')
            print sys.path
            try:
                import java
            except ImportError:
                return None
            try:
                from src.test import TestTTS
                return TestTTS()
  
            except java.lang.UnsatisfiedLinkError:
                pass
            except ImportError, err:
                print >> sys.stderr, 'cannot find org.test.TestTTs: %s' % str(err)
            except Exception, e: 
                print e
                import code
                code.InteractiveConsole().interact()
                
            return None
  
            sys.exit(1)

    def restore_newlines(self, s):
        return s.replace(NEWLINE_ENCODING, '\n')

    def default_cmd_processing(self, buf, cmd, args): 
        """Handle nbkey commands not matched with a 'cmd_<keyName>' method.""" 
        info('defalut_cmd_processing: nbkey: %s', (cmd, args, buf))
        if not self.speech:
            info('default_cmd failed, phonemic not running.')
        try: 
            phonemic_method = getattr(self.speech, cmd)
        except AttributeError:
            raise PhonimCommandNotExist()
        if cmd in  ['setVoice', 'setSpeechEnabled', 'setTextToSpeechEngine']:
            raise PhonimCommandNotImplemented()
        # handle the set/get/speak commands differently i.e. speak getter's return val

        # Property setter: floats
        if cmd[:3] == 'set': 
            try:
                float_arg = float(args)
            # volume etc. must be between 0 and 1.
                if float_arg < 0: float_arg = 0
                if float_arg > 1: float_arg = 1 


                if phonemic_method(float_arg):
                    self._speak('Phonemic succesfully %s to %s' 
                         % ( cmd, str(float_arg) ) )
                else: 
                    self._speak('Phonemic failed to  %s to %s' 
                         % ( cmd, str(float_arg) ) )
            except VauleError: 
                raise PhonimBadArgumentException()

        # Speech
        elif cmd[:5] == 'speak':
            with_newlines = self.restore_newlines(args)
            phonemic_method(with_newlines)

        # Info methods (get/is/supports)
        else:
            self._speak('Phonemic %s returned %s'  
                      % (cmd, str(phonemic_method())) )
    

    # this should speak one character at a time
    def cmd_speakChar(self, buf, args):
        #fixed = restore_newlines(args)
        fixed = args
        self.speech.speakBlocking(fixed, SpeechPriority.MEDIUM, RequestType.CHAR)

    def _speak(self, string):
        if self.speech:
            self.speech.speak(string)
        else:
            sys.stdout.write('speak> "' + string + '"' + os.linesep)

    def speak(self, string):
        self._speak(string)
    




    
# this is now covered by generic phonemic method handler
#    def cmd_speak(self, buf, args):
#        self._speak(args)

#=============
# Preferences
#=============
    '''
    # args: string field, float value
    @parse_args
    def cmd_setPhonemicValue(self, buf, args):
      pass

    @parse_args
    def cmd_speakPhonemicValue(self, buf, args):
      pass

    # args: float value
    @float_args
    def cmd_setSpeed(self, buf, args):
      pass
    # args: float val
    @float_args

    def cmd_setPitch(self, buf, args):
      pass
    # args: float val
    @float_args
    def cmd_setVolume(self, buf, args):
      pass

    # args: string VoiceName
    def cmd_setVoice(self, buf, args):
      pass

#==============
# Speech commands
#==============

    @parse_args
    def cmd_speak(self, buf, args):
      """args->
      char : bool, 
      command : stop, pause, resume, etc 
      priority : int 
      blocking : bool 
      textToSpeak : string #may contain encoded newlines"""

      pass


    # Speak one character at a time
    # args: string text
    @parse_args
    def cmd_speakChar(self, buf, args):
      pass

    @parse_args
    def cmd_speakBlocking(self, buf, args):
      pass

    @parse_args
    def cmd_controlPhonemic(self, buf, args):
      """args: stop, pause, resume, etc
      configurable behavior for how to handle case where OS/screenreader does not allow that operation. e.g. silent=true"""
      pass
    #Screenreader-dependent?
    @phonemic_optional
    def cmd_stopSpeech(self, buf, args):
      self.speech.stopSpeech()
      pass

    #Screenreader-dependent
    @phonemic_optional
    def cmd_pauseSpeech(self, buf, args):
      pass

    #Screenreader-dependent
    @phonemic_optional
    def cmd_resumeSpeech(self, buf, args):
      pass

    #  not optional
    def cmd_respeak(self, buf, args):
      self.speech.respeak() 
      pass

    #@sideffect: copy most resent spoken text to system clipboard
    def cmd_copyToClipboard(self, buf, args):
      pass


    def cmd_speakVimValue(self, buf, args):
      """prioirty, etc. type : status,warning,error"""
      self.speech.speak(args)
      pass

    # args: string status-message
    def cmd_speakStatus(self, buf, args):
      pass

    # args: string warning-message
    def cmd_speakWarning(self, buf, args):
      pass

    # args: string error-message
    def cmd_speakError(self, buf, args):
      pass
    '''
#=======================
#Custom events triggered by autocommands
#=======================
    # args: string currentline of the buffer
    # triggered by CursorMoved autocmd
    def cmd_CursorMoved(self, buf, args):
      pass

    # args: string currentline of the buffer
    # triggered by CursorMovedI autocmd
    def cmd_CursorMovedI(self, buf, args):
      pass


#=======================
#External processes
#=======================
    # see process.py
    # no parsed_args decorator b/c we doing something diff. 
    def cmd_run(self, buf, args):
      pass





#@params: msg=PMessage from :nbkey command 
#@return: None
#@Sideeffect: speak or execute user preference change

    # These fields will have different values if, for example, a command is sent to change Phonemic's volume or other properties

