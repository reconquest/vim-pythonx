py3 import px.langs

py3 import px.common
py3 import px.autocommands
py3 import px.snippets

let g:pythonx_go_info_mode = get(g:, 'pythonx_go_info_mode', 'gocode')

let g:pythonx_highlight_completion = get(g:, 'pythonx_highlight_completion', 1)
execute "py3"  "px.snippets.option_highlight_completion = " . g:pythonx_highlight_completion

function! s:RememberBlockVisualState()
    let b:_px_langs_go_autoimport_block_visual = 1
    call pythonx#unmap_autoimport()
    return 'I'
endfunction

function! s:RemoveBlockVisualState()
    call pythonx#map_autoimport()
    unlet! b:_px_langs_go_autoimport_block_visual
endfunction

function! pythonx#autoimport()
    if !exists('b:_px_langs_go_autoimport_block_visual')
        execute "py3" "px.langs.go.autoimport_at_cursor()"
    endif
    return ''
endfunction!

func! pythonx#map_autoimport()
   inoremap <silent> <buffer> . <C-\><C-O>:call pythonx#autoimport()<CR>.
endfunc!

func! pythonx#unmap_autoimport()
    silent! iunmap <buffer> .
endfunc!

augroup px_langs_go
    au!
    au FileType go py3 import px.langs.go

    au FileType go vnoremap <expr> I <SID>RememberBlockVisualState()
    au FileType go au InsertLeave <buffer>
            \ call <SID>RemoveBlockVisualState()

    au FileType go call pythonx#map_autoimport()
augroup END

function! pythonx#CompleteIdentifier()
    py3 px.autocommands.enable_identifier_completion_auto_reset()
    if g:pythonx_highlight_completion == 1
        py3 px.autocommands.enable_highlight_auto_clear()
    endif
    py3 px.common.wrap_for_filetype('complete_identifier')()
    if g:pythonx_highlight_completion == 1
        py3 px.common.highlight_completion()
    endif
endfunction!

"inoremap <silent> <C-L> <C-\><C-O>:call pythonx#CompleteIdentifier()<CR>
"smap <C-L> <BS><C-L>
"
"pyx px.autocommands.enable_cursor_moved_callbacks()

command! -nargs=0 -bar
    \ PythonxGoAutoimportResetCache
    \ py3 px.langs.go.autoimport_reset_cache()
