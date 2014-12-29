

Phonim
=======

Currently in development, and documentation is incomplete.

Make vim speak using the cross-platform java library Phonemic https://github.com/hcarver/phonemic

Jython implmementation of the netbeans protocol provided by the vimoir project https://code.google.com/p/vimoir/

phonim.vim to fire off nbkey messages on user actions using vim autocommands

phonemic.py is our client module responsible for handling the netbeans messages. Most of the work goes here and in phonim.vim

We can hook into insert/remove netbeans events, but have to handle normal mode movement using autocommands (there is no netbeans event for normal mode movement). The limits of netbeans require us to create our own protocol and pass the current line to the client.


Protocol:

:nbkey command#col#lnum#textofline

users can send commands to customize on the fly, etc. more to come. Currently the whole message is read indiscriminately.


Usage
======

Commandline:

`$ jython netbeans.py`

You can optionally pass jython the directory to phonemic.jar

`$ jython netbeans.py lib/phonemic.jar`

From your running vim instance, execute the following:

`:nbstart`

`:source /path/to/ftplugin/phonim.vim`

and stop:

`:nbclose`

Process.py
==========
Allows user to run processes in a seperate thread and get the results. Currently these results are piped into the beginning of the file or into a text balloon (which only appears if vim is run in a GUI!) but I think this could be piped to a new vim buffer or to phonemic. Note this does not trigger the netbeans text-inserted event, nor does it move the user's cursor to the new text. This allows user to get the output of some arbitrary code execution / system process spoken to them. Not also this is asynchronous.
                                                                
This capability opens up som eadditional uses (i.e. vim could be used as a defacto screenreader for the terminal, for example). As such the client class has more responsibility.  

The thread sends a message back to vim using the insert text funciton. 'insert' is the name of the command, and the parameters are of form   "offset<int> <space> text<string>" i.e. ' 0 foo '

The client in process.py uses the netbeans method: send_function(buf, 'insert', params, observer)
where observer implements some function "update"

Possible replies:
123             no problem
123 !message    failed

Probably we should change this to append to the current offset, or optionally into a new buffer. We can force netbeans to create its own buffer (using a IDE -> Vim command) or by creating a buffer within the VimL (vim-script).
Notes
=====

Currently does not work when vim is in Read-only mode.

I have encountered some kind of bug where a netbeans command including newline/emptyline crashes the client, but things seem to be working now.

Will push the Java implementation once I get it organized, but will be using this for prototyping because development is faster
