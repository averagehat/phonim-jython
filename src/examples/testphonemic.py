import unittest
from phonemic import Phonemic
import sys

class PhonemicTest(unittest.TestCase):

  def testIO(self):
    print "foo"
    print "bar"
    print 'line3'
    output = sys.stdout.getvalue().strip()
    assert output == 'foo\nbar\nline3'
  
  def prompt_wrap(self, string):
    PROMPT = 'speak> "'
    return PROMPT + string + '"'
  
  def test_parse_msg(self):
    pho = Phonemic(None) # pass no netbeans socket
    raw_msg = '#'.join(['speak', '1', '13', 'innocent_line'])
    parsed = pho.parse_msg(raw_msg)
    assert parsed.cmd == 'speak'
    assert parsed.col == 1
    assert parsed.lnum == 13
    assert parsed.line == 'innocent_line'

  def test_execute_cmd(self):
    pho = Phonemic(None) # pass no netbeans socket
    raw_msg = '#'.join(['speak', '1', '13', 'test speech'])
    pho.execute_cmd(raw_msg)
    output = sys.stdout.getvalue().strip()
    assert output == self.prompt_wrap('test speech')

  def test_get_cursor_change(self):
    pho = Phonemic(None) # pass no netbeans socket
    raw_msg = '#'.join(['speak', '1', '13', ''])
    parsed = pho.parse_msg(raw_msg)
    dx0, dy0 = pho.get_cursor_change(parsed)
    assert dx0 == 0
    assert dy0 == 12
    msg2 = pho.parse_msg('#'.join(['speak', '5', '13', '']))
    dx2, dy2 = pho.get_cursor_change(msg2)
    assert dx2 == 4
    assert dy2 == 0
    msg3 = pho.parse_msg('#'.join(['speak', '-2', '13', '']))
    self.assertRaises(ValueError, pho.get_cursor_change, msg3)
        

if __name__ == '__main__': 
   unittest.main(module=__name__, buffer=True, exit=False)
   
