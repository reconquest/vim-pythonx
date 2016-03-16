py import px.langs

augroup px_langs_go
    au!
    au FileType go py import px.langs.go
    au FileType go inoremap
        \ <silent> <buffer> . <C-\><C-O>:py px.langs.go.autoimport()<CR>.
augroup END

inoremap <silent> <C-L> <C-\><C-O>:call px#CompleteIdentifier()<CR>
smap <C-L> <BS><C-L>

py import px.common
py import px.autocommands

function! px#CompleteIdentifier()
    py px.autocommands.enable_identifiers_completion_auto_reset()
    py px.common.wrap_for_filetype('complete_identifier')()
    py px.common.highlight_completion()
endfunction!

py px.autocommands.enable_cursor_moved_callbacks()
