"------------------------------------------------------------
"
"
"  Phonim Vim Plugin
"
"  Using the netbeans protocol
"  github.com/averagehat
"-------------------------------------------------------------


" :map ` yw | nbkey speak arg



"map <expr>  `  Loop()
"---------
" Functions
" --------
function! NbExecute(msg)
  execute 'nbkey ' . a:msg
  echo 'nbkey ' . a:msg
endfunction

function! SpeakLine()
  let args = ['speak', line('.'), col('.'), getline('.', '.')[0]]
  let msg = join(args, '#')
  call NbExecute(msg)
endfunction


"---------
" Events
" --------

" hook to normal mode movements
:autocmd CursorMoved * :call SpeakLine()


