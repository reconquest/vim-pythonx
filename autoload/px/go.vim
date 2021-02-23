let s:sock_type = (has('win32') || has('win64')) ? 'tcp' : 'unix'

function! px#go#get_info(identifier) abort
    if g:pythonx_go_info_mode == 'coc'
        return px#go#coc_info()
    else
        return px#go#gocode_info(a:identifier)
    fi
endfunc!

func! px#go#coc_info() abort
    let result = CocAction('getDefinition')
    if result == ''
        return ''
    endif

    let lines = split(result, '\n')
    if len(lines) < 2
        return result
    endif

    " first line will be markdown-ish stuff: ```go
    return lines[1]
endfunc!

function! px#go#gocode_info(identifier) abort
  let offset = go#util#OffsetCursor()
  let filename = s:gocodeCurrentBuffer()
  let result = s:gocodeCommand('autocomplete',
        \ [s:gocodeCurrentBufferOpt(filename), '-f=godit'],
        \ [expand('%:p'), offset])
  call delete(filename)

  " first line is: Charcount,,NumberOfCandidates, i.e: 8,,1
  " following lines are candiates, i.e:  func foo(name string),,foo(
  let out = split(result, '\n')

  " no candidates are found
  if len(out) == 1
    return ""
  endif

  " to many candidates are available, pick one that maches the word under the
  " cursor
  let infos = []
  for info in out
    call add(infos, split(info, ',,')[0])
  endfor

  let wordMatch = '\C\<' . a:identifier . '\>'
  " escape single quotes in wordMatch before passing it to filter
  let wordMatch = substitute(wordMatch, "'", "''", "g")
  let filtered =  filter(infos, "v:val =~ '".wordMatch."'")

  if len(filtered) == 1
    return filtered[0]
  endif

  return ""
endfunction

function! s:gocodeCommand(cmd, preargs, args) abort
  for i in range(0, len(a:args) - 1)
    let a:args[i] = go#util#Shellescape(a:args[i])
  endfor
  for i in range(0, len(a:preargs) - 1)
    let a:preargs[i] = go#util#Shellescape(a:preargs[i])
  endfor

  let bin_path = go#path#CheckBinPath("gocode")
  if empty(bin_path)
    return
  endif

  " we might hit cache problems, as gocode doesn't handle well different
  " GOPATHS: https://github.com/nsf/gocode/issues/239
  let old_gopath = $GOPATH
  let old_goroot = $GOROOT
  let $GOPATH = go#path#Detect()
  let $GOROOT = go#util#env("goroot")

  let socket_type = get(g:, 'go_gocode_socket_type', s:sock_type)
  let cmd = printf('%s -sock %s %s %s %s',
        \ go#util#Shellescape(bin_path),
        \ socket_type,
        \ join(a:preargs),
        \ go#util#Shellescape(a:cmd),
        \ join(a:args)
        \ )

  let result = go#util#System(cmd)
  let $GOPATH = old_gopath
  let $GOROOT = old_goroot

  if go#util#ShellError() != 0
    return "[\"0\", []]"
  else
    if &encoding != 'utf-8'
      let result = iconv(result, 'utf-8', &encoding)
    endif
    return result
  endif
endfunction

function! s:gocodeCurrentBufferOpt(filename) abort
  return '-in=' . a:filename
endfunction

function! s:gocodeCurrentBuffer() abort
  let file = tempname()
  call writefile(go#util#GetLines(), file)
  return file
endfunction

function! px#go#GetPackagePath() abort
  let command = "go list"
  let out = go#tool#ExecuteInDir(command)
  if go#util#ShellError() != 0
      return -1
  endif

  return split(out, '\n')[0]
endfunction

" This is a modified version of vim-go's SwitchImport func
" This function doesn't interact with the filesystem and just adds a given path to
" the imports section
function! px#go#import(path) abort
  let view = winsaveview()
  let path = substitute(a:path, '^\s*\(.\{-}\)\s*$', '\1', '')

  " Quotes are not necessary, so remove them if provided.
  if path[0] == '"'
    let path = strpart(path, 1)
  endif
  if path[len(path)-1] == '"'
    let path = strpart(path, 0, len(path) - 1)
  endif

  " if given a trailing slash, eg. `github.com/user/pkg/`, remove it
  if path[len(path)-1] == '/'
    let path = strpart(path, 0, len(path) - 1)
  endif

  if path == ''
    echoe 'Import path not provided'
    return
  endif

  " Extract any site prefix (e.g. github.com/).
  " If other imports with the same prefix are grouped separately,
  " we will add this new import with them.
  " Only up to and including the first slash is used.
  let siteprefix = matchstr(path, "^[^/]*/")

  let qpath = '"' . path . '"'
  let qlocalpath = qpath
  let indentstr = 0
  let packageline = -1 " Position of package name statement
  let appendline = -1  " Position to introduce new import
  let deleteline = -1  " Position of line with existing import
  let linesdelta = 0   " Lines added/removed

  " Find proper place to add/remove import.
  let line = 0
  while line <= line('$')
    let linestr = getline(line)

    if linestr =~# '^package\s'
      let packageline = line
      let appendline = line

    elseif linestr =~# '^import\s\+(\+)'
      let appendline = line
      let appendstr = qlocalpath
    elseif linestr =~# '^import\s\+('
      let appendstr = qlocalpath
      let indentstr = 1
      let appendline = line
      let firstblank = -1
      let lastprefix = ""
      while line <= line("$")
        let line = line + 1
        let linestr = getline(line)
        let m = matchlist(getline(line), '^\()\|\(\s\+\)\(\w\+\s\+\)\="\(.\+\)"\)')
        if empty(m)
          if siteprefix == ""
            " must be in the first group
            break
          endif
          " record this position, but keep looking
          if firstblank < 0
            let firstblank = line
          endif
          continue
        endif
        if m[1] == ')'
          " if there's no match, add it to the first group
          if appendline < 0 && firstblank >= 0
            let appendline = firstblank
          endif
          break
        endif
        let lastprefix = matchstr(m[4], "^[^/]*/")
        let appendstr = m[2] . qlocalpath
        let indentstr = 0
        if m[4] == path
          let appendline = -1
          let deleteline = line
          break
        elseif m[4] < path
          " don't set candidate position if we have a site prefix,
          " we've passed a blank line, and this doesn't share the same
          " site prefix.
          if siteprefix == "" || firstblank < 0 || match(m[4], "^" . siteprefix) >= 0
            let appendline = line
          endif
        elseif siteprefix != "" && match(m[4], "^" . siteprefix) >= 0
          " first entry of site group
          let appendline = line - 1
          break
        endif
      endwhile
      break

    elseif linestr =~# '^import '
      if appendline == packageline
        let appendstr = 'import ' . qlocalpath
        let appendline = line - 1
      endif
      let m = matchlist(linestr, '^import\(\s\+\)\(\S*\s*\)"\(.\+\)"')
      if !empty(m)
        if m[3] == path
          let appendline = -1
          let deleteline = line
          break
        endif
        if m[3] < path
          let appendline = line
        endif
        let appendstr = 'import' . m[1] . qlocalpath
      endif

    elseif linestr =~# '^\(var\|const\|type\|func\)\>'
      break

    endif
    let line = line + 1
  endwhile

  " Append or remove the package import, as requested.
  if deleteline != -1
    return
  elseif appendline == -1
    return
  else
    if appendline == packageline
      call append(appendline + 0, '')
      call append(appendline + 1, 'import (')
      call append(appendline + 2, ')')
      let appendline += 2
      let linesdelta += 3
      let appendstr = qlocalpath
      let indentstr = 1
      call append(appendline, appendstr)
    elseif getline(appendline) =~# '^import\s\+(\+)'
      call setline(appendline, 'import (')
      call append(appendline + 0, appendstr)
      call append(appendline + 1, ')')
      let linesdelta -= 1
      let indentstr = 1
    else
      call append(appendline, appendstr)
    endif
    execute appendline + 1
    if indentstr
      execute 'normal! >>'
    endif
    let linesdelta += 1
  endif

  " Adjust view for any changes.
  let view.lnum += linesdelta
  let view.topline += linesdelta
  if view.topline < 0
    let view.topline = 0
  endif

  " Put buffer back where it was.
  call winrestview(view)

endfunction
