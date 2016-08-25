py import px.langs

function! s:RememberBlockVisualState()
    let b:_px_langs_go_autoimport_block_visual = 1
    return 'I'
endfunction


function! pythonx#autoimport()
    if !exists('b:_px_langs_go_autoimport_block_visual')
        execute "py" "px.langs.go.autoimport_at_cursor()"
    endif
endfunction!


augroup px_langs_go
    au!
    au FileType go py import px.langs.go

    au FileType go vnoremap <expr> I <SID>RememberBlockVisualState()
    au FileType go au InsertLeave <buffer>
            \ unlet! b:_px_langs_go_autoimport_block_visual
    au FileType go inoremap
        \ <silent> <buffer> . <C-O>:call pythonx#autoimport()<CR>.
augroup END

inoremap <silent> <C-L> <C-\><C-O>:call pythonx#CompleteIdentifier()<CR>
smap <C-L> <BS><C-L>

py import px.common
py import px.autocommands

function! pythonx#CompleteIdentifier()
    py px.autocommands.enable_identifier_completion_auto_reset()
    py px.autocommands.enable_highlight_auto_clear()
    py px.common.wrap_for_filetype('complete_identifier')()
    py px.common.highlight_completion()
endfunction!

py px.autocommands.enable_cursor_moved_callbacks()

command! -nargs=0 -bar
    \ PythonxGoAutoimportResetCache
    \ py px.langs.go.autoimport_reset_cache()
