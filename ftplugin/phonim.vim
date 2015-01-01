"------------------------------------------------------------
"
"
"  Phonim Vim Plugin
"
"  Using the netbeans protocol
"  github.com/averagehat
"-------------------------------------------------------------

"---------
" Functions
" --------
"  DEPRECATED
"function! NbExecute(msg)
"  execute 'nbkey ' . a:msg
"  echo 'nbkey ' . a:msg
"endfunction
"
"function! SpeakLine()
"  let args = ['speak', line('.'), col('.'), getline('.', '.')[0]]
"  let msg = join(args, '#')
"  call NbExecute(msg)
"endfunction
"
"" hook to normal mode movements
":autocmd CursorMoved * :call SpeakLine()


"nmap <silent> <C-i> :set opfunc=NetBeansCommand<CR>g@
" NetBeansCommand is not working as an operator function.
" see :h g@  or http://mikep.info.tm/category/projects.html for defining operator functions
"
"
" Sends a string (replacing newlines with sapces) to netbeans via the :nbkey
" command
      
fun! SpeakBlocking(s)
  call Speak(a:s, 'speakBlocking')
endfun

fun! SpeakNonBlocking(s)
  call Speak(a:s, 'speak')
endfun

" speechType = speakBlocking or speak
fun! Speak(text, speechType) 
  "netbeans protocol terminates at newlines!
  let l:sanitized = substitute(a:text, '\n', ' ', 'g') 
  silent exe 'nbkey ' . speechType . ' ' .  sanitized
endfun

"note the allowedCommand list is incomplete.
let s:allowedCommands =  ['speak', 'speakBlocking', 'getVolume'] "etc.

" incomplete, demonstrates optional arguments
fun! NetBeansCommand(cmd, ...)
  if (index(s:allowedCommands, a:cmd) < 0)
    echoerr a:cmd . "is not a vaild Command!"
    return "" " we can also notify by speaking.
  else 
    if a:0 > 0 "a[0] "holds number of optional arguments
      let l:arg = a:1 "grab the first (only optional) argument
"      silent exe 'echo ' . a:cmd . ' ' won't work because doesn't wrap them in quotes.
      echomsg  a:cmd . ' ' . l:arg
    else
      echomsg  a:cmd
    endif
  endif
endfun
  
" Autocommands time, with error checking.
" soon to come . . . 
"au CursorMoved * echo "foo" 
