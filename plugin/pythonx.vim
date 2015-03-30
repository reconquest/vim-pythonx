py import px.all

augroup vim_pythonx_go
    au!
    au FileType go py import px.go
    au FileType go inoremap <buffer> . <C-\><C-O>:py px.go.autoimport()<CR>.
augroup END

augroup vim_pythonx_php
    au!
    au FileType php py import px.php
augroup END

inoremap <C-L> <C-\><C-O>:py px.all.wrap_for_filetype('cycle_by_var_name')()<CR>
smap <C-L> <BS><C-L>
