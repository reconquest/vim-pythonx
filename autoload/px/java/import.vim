func! px#java#import#callback(candidates)
    let b:px_java_import_callback_candidates = a:candidates
    let l:result = pyeval('px.langs.java.choose_import(vim.current.window.buffer.vars["px_java_import_callback_candidates"])')
    unlet b:px_java_import_callback_candidates
    return result
endfunc!
