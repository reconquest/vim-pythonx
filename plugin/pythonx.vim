py import px.all

augroup vim_pythonx_go
    au!
    au FileType go py import px.go
    au FileType go inoremap <silent> <buffer> . <C-\><C-O>:py px.go.autoimport()<CR>.

    au FileType go :autocmd! vim_pythonx_go CursorMovedI <buffer>
        \ call PxCompleteVarResetState('CursorMovedI')

    au FileType go :autocmd! vim_pythonx_go InsertLeave <buffer>
        \ call PxCompleteVarResetState('InsertLeave')
augroup END

augroup vim_pythonx_php
    au!
    au FileType php py import px.php
augroup END

inoremap <silent> <C-L> <C-\><C-O>:call PxCompleteVar()<CR>
smap <C-L> <BS><C-L>

let g:_px_go_complete_var_should_skip_cursor_moved_i = 0
let g:_px_go_complete_var_should_skip_insert_leave = 0

function! PxCompleteVarResetState(autocmd)
    if a:autocmd == 'CursorMovedI'
        if g:_px_go_complete_var_should_skip_cursor_moved_i == 1
            let g:_px_go_complete_var_should_skip_cursor_moved_i = 0
            return
        en
    en

    if a:autocmd == 'insertleave'
        if g:_px_go_complete_var_should_skip_insert_leave == 1
            let g:_px_go_complete_var_should_skip_insert_leave = 0
            return
        en
    en

    py px.all.reset_complete_var_state()
endfunction!

function! PxCompleteVar()
    let g:_px_go_complete_var_should_skip_cursor_moved_i = 1
    let g:_px_go_complete_var_should_skip_insert_leave = 1

    py px.all.wrap_for_filetype('complete_var')()
endfunction!
