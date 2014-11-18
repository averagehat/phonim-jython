

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

You need to pass jython the directory to phonemic.jar

`$ jython netbeans.py lib/phonemic.jar`

From your running vim instance, execute the following:

`:nbstart`

`:source /path/to/ftplugin/phonim.vim`

and stop:

`:nbclose


Notes
=====

I have encountered some kind of bug where a netbeans command including newline/emptyline crashes the client, but things seem to be working now.

