pyx import px.langs

pyx import px.common
pyx import px.autocommands
pyx import px.snippets

let g:pythonx_highlight_completion = get(g:, 'pythonx_highlight_completion', 1)
execute "pyx"  "px.snippets.option_highlight_completion = " . g:pythonx_highlight_completion

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
        execute "py" "px.langs.go.autoimport_at_cursor()"
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
    au FileType go pyx import px.langs.go

    au FileType go vnoremap <expr> I <SID>RememberBlockVisualState()
    au FileType go au InsertLeave <buffer>
            \ call <SID>RemoveBlockVisualState()

    au FileType go call pythonx#map_autoimport()
augroup END

function! pythonx#CompleteIdentifier()
    pyx px.autocommands.enable_identifier_completion_auto_reset()
    if g:pythonx_highlight_completion == 1
        pyx px.autocommands.enable_highlight_auto_clear()
    endif
    pyx px.common.wrap_for_filetype('complete_identifier')()
    if g:pythonx_highlight_completion == 1
        pyx px.common.highlight_completion()
    endif
endfunction!

"inoremap <silent> <C-L> <C-\><C-O>:call pythonx#CompleteIdentifier()<CR>
"smap <C-L> <BS><C-L>
"
"pyx px.autocommands.enable_cursor_moved_callbacks()

command! -nargs=0 -bar
    \ PythonxGoAutoimportResetCache
    \ pyx px.langs.go.autoimport_reset_cache()
