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

from netbeans import NetbeansClient
from subprocess import Popen, PIPE, STDOUT
from threading import Thread

class Process(NetbeansClient):
    """Run a process from an ':nbkey run' command in a worker thread.

    This class extends NetbeansClient so as to implement only the methods it is
    interested in.
    The process is run in a thread so as not to block I/O on the Netbeans
    socket. On the process termination, the process output from stdout and
    stderr is displayed in a Vim balloon.
    For example to run a python command that sleeps 2 seconds and prints 'Ok',
    run in Vim:

        :nbkey run python -c "import time; time.sleep(2); print \"Ok\""

    """

    def cmd_run(self, buf, args):
        """Process a keyAtPos event with the 'run' keyName."""
        class Worker(object):
            def __init__(self):
                try:
                    output = (Popen(split_quoted_string(args), shell=False,
                                stdout=PIPE, stderr=STDOUT).communicate()[0])
                except OSError, err:
                    send_cmd(None, 'showBalloon', quote(str(err)))
                else:
                    msg = "Result of process '%s':\n%s" % (args, output)
                    send_cmd(None, 'showBalloon', quote(msg))

        # nbsock is the netbeans socket (set in the super class constructor)
        split_quoted_string = self.nbsock.split_quoted_string
        quote = self.nbsock.quote
        send_cmd = self.nbsock.send_cmd
        Thread(target=Worker).start()

