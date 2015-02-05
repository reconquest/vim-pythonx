py import util

augroup vim_pythonx_go
    au!
    au FileType go py import go
    au FileType go inoremap <C-L> <C-\><C-O>:py go.cycle_by_var_name()<CR>
    au FileType go smap <C-L> <BS><C-L>
augroup END

augroup vim_pythonx_php
    au!
    au FileType php py import php
    au FileType php inoremap <C-L> <C-\><C-O>:py php.cycle_by_var_name()<CR>
    au FileType php smap <C-L> <BS><C-L>
augroup END
