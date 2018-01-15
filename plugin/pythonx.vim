py import px.langs

py import px.common
py import px.autocommands
py import px.snippets

let g:pythonx_highlight_completion = get(g:, 'pythonx_highlight_completion', 1)
execute "py"  "px.snippets.option_highlight_completion = " . g:pythonx_highlight_completion

function! s:RememberBlockVisualState()
    let b:_px_langs_go_autoimport_block_visual = 1
    return 'I'
endfunction

function! pythonx#autoimport()
    if !exists('b:_px_langs_go_autoimport_block_visual')
        execute "py" "px.langs.go.autoimport_at_cursor()"
    endif
    return ''
endfunction!

augroup px_langs_go
    au!
    au FileType go py import px.langs.go

    au FileType go vnoremap <expr> I <SID>RememberBlockVisualState()
    au FileType go au InsertLeave <buffer>
            \ unlet! b:_px_langs_go_autoimport_block_visual
    au FileType go inoremap
        \ <silent> <buffer> . <C-\><C-O>:call pythonx#autoimport()<CR>.
augroup END

function! pythonx#CompleteIdentifier()
    py px.autocommands.enable_identifier_completion_auto_reset()
    if g:pythonx_highlight_completion == 1
        py px.autocommands.enable_highlight_auto_clear()
    endif
    py px.common.wrap_for_filetype('complete_identifier')()
    if g:pythonx_highlight_completion == 1
        py px.common.highlight_completion()
    endif
endfunction!

inoremap <silent> <C-L> <C-\><C-O>:call pythonx#CompleteIdentifier()<CR>
smap <C-L> <BS><C-L>

py px.autocommands.enable_cursor_moved_callbacks()

command! -nargs=0 -bar
    \ PythonxGoAutoimportResetCache
    \ py px.langs.go.autoimport_reset_cache()
