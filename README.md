Phonim
=======

Currently in development, and documentation is incomplete.

Make vim speak using the cross-platform java library Phonemic https://bitbucket.org/stefika/phonemic/

Jython implmementation of the netbeans protocol provided by the vimoir project https://code.google.com/p/vimoir/



`phonemic.py` is our client module responsible for handling the netbeans messages. Most of the work goes here and in `phonim.vim`. `phonim.vim` triggers vimscript (VimL) to fire off nbkey messages on user actions using vim autocommands.
We can hook into insert/remove netbeans events, but have to handle normal mode movement using autocommands (there is no netbeans event for normal mode movement). The limits of netbeans require us to create our own protocol and pass the current line to the client.

Users can send commands to customize on the fly, etc. more to come. 

###Protocol:

```vim
:nbkey {phonemic command} {optional argument}  
:nbkey speakBlocking   foo 
:nbkey setVolume  .5 
:nbkey getPitch 
```

The `nbkey` triggers the newDotAndMark, keyCommand and keyAtPos messages. We are interested solely in `keyAtPos`, becasue vim automatically packages the cursor position and the contents of the message. The protocol looks (roughly) like:


```
11:keyAtPos=123 "The Message or 'key name' " lnum/col
```

You can get more information by starting phonim with the `--debug` flag, and additionaly by compiling vim with with the `NBDEBUG` flag (see `:h netbeans-debugging`).




###VimL
See [mikep.info.tm/category/projects.html](http://mikep.info.tm/category/projects.html) for an overview of the vim language concepts involved in this project.Particularly interesting is the information on the bottom about custom operators.
We will use custom operators in vim-script to allow users to select their speech using vim motions, and send this to phonemic.

###Usage
Commandline:

`$ jython netbeans.py --conf conf --debug`

You can optionally pass jython the directory to phonemic.jar

`$ jython netbeans.py lib/phonemic.jar --conf conf`

From your running vim instance, execute the following:

`:nbstart`

`:source /path/to/ftplugin/phonim.vim`

and stop:

`:nbclose`

###Process.py
Allows user to run processes in a seperate thread and get the results. Currently these results are piped into the beginning of the file or into a text balloon (which only appears if vim is run in a GUI!) but I think this could be piped to a new vim buffer or to phonemic. Note this does not trigger the netbeans text-inserted event, nor does it move the user's cursor to the new text. This allows user to get the output of some arbitrary code execution / system process spoken to them. Not also this is asynchronous.
                                                                
This capability opens up som eadditional uses (i.e. vim could be used as a defacto screenreader for the terminal, for example). As such the client class has more responsibility.  

The thread sends a message back to vim using the insert text funciton. 'insert' is the name of the command, and the parameters are of form   "offset<int> <space> text<string>" i.e. ' 0 foo '

The client in process.py uses the netbeans method: send_function(buf, 'insert', params, observer)
where observer implements some function "update"

Possible replies:
123             no problem
123 !message    failed

Probably we should change this to append to the current offset, or optionally into a new buffer. We can force netbeans to create its own buffer (using a IDE -> Vim command) or by creating a buffer within the VimL (vim-script).

###Next Steps
I am going to try hooking the autocommands. We will use CursorMoved to track user movement and read new content, and CursorHold to check for errors. Something like:

```vim
au CursorMoved * nbkey getline('.')  " replaced with phonim.vim function
```

The Netbeans client is responsible for determining where the user moved in relation to where they were (i.e., did they move to a new line? Did they switch buffers/windows?) and picking the right text to speak (all or some of the line sent by the `nbkey` command. 

We also want to do error checking. (We might, too, want to check when new buffers are opened, saved, etc., in case these do not belong to netbeans). 

```vim
au CursorHold * call CheckMessages()
```

```vim
let g:lastError = ""
function CheckMessages() 
  if (g:lastError == v:errmsg)
    "do nothing
  else 
    let g:lastError = v:errmsg
    speak(g:lastError)
  endif
endfun
```  
Where we are interested in the following variables (you can check their values with `:let v:` : 
```vim
v:errmsg
v:statusmsg
v:shell_error
v:warningmsg
```
Note that we cannot overwrite these variables. 


###Testing
Functional testing with the vim-python module. Possibly using vader, but note that vader does not trigger autocommands correctly. I have created a mock `speech` object which implements TextToSpeech.java. Rather than speaking this writes to a file. So the test framework will trigger commands with python and then check the file for the expected output. (including recorded volume, speaking speed, etc.). I have confirmed that actions by the python script will trigger autocommands (cursormoved) and netbeans events like "text inserted." 

```python
vim.current.window.cursor = (row, column)  -> triggers CursorMoved.
vim.current.window.buffer.append('foo')   -> triggers ONE netbeans insert event, and possibly a second "empty byte" or "end-of-line" insert event.
vim.command('nbkey speakBlocking  <sometext>')  -> call phonemic from within python
```

Notes
=====

Currently does not work when vim is in Read-only mode.

I have encountered some kind of bug where a netbeans command including newline/emptyline crashes the client, but things seem to be working now.

Will push the Java implementation once I get it organized, but will be using this for prototyping because development is faster

There are sometimes crashes because of file writes or other reasons. I also encountered a bug that crashed vim when deleting a large number of lines. This triggered an infinite loop in vim. However, I believe the problem was related to running vim in-terminal, and have not encountered the same problem in MacVim. Also, at times NetBeans (well, vim) will not let you save your file. I need to understand better how "buffer ownership" works, because the netbeans events will only work properly in netbeans-owned buffers.  
