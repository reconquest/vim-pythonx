let s:sock_type = (has('win32') || has('win64')) ? 'tcp' : 'unix'

function! px#go#GetInfo(identifier) abort
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

  " only one candiate is found
  if len(out) == 2
    return split(out[1], ',,')[0]
  endif

  " to many candidates are available, pick one that maches the word under the
  " cursor
  let infos = []
  for info in out[1:]
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
