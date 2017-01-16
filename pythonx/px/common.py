# coding=utf8

import importlib

import px.cursor
import px.cursor.callbacks
import px.autocommands
import px.completion
import px.highlight
import px.buffer

_DefaultCompleter = px.completion.IdentifierCompleter()

_ActiveCompleter = None

_DefaultHighlighter = px.highlight.Highlighter()

_DefaultCursorMovedCallbackCaller = px.cursor.callbacks.MovedCallbackCaller()


def wrap_for_filetype(function_name):
    common_module = module = importlib.import_module('px.common')

    try:
        module = importlib.import_module(
            'px.langs.' + str(px.buffer.get().options['filetype'])
        )
    except ImportError:
        module = common_module
    except KeyError:
        module = common_module

    try:
        return getattr(module, function_name)
    except AttributeError:
        return getattr(common_module, function_name)

def get_active_identifier_skipper():
    def active_skipper(identifier):
        return get_active_completer()._default_skipper(identifier)

    return active_skipper


def get_identifier_completion(identifiers=[],
        should_skip=get_active_identifier_skipper()):
    return get_active_completer().get_identifier_completion(
        px.buffer.get(),
        px.cursor.get(),
        identifiers,
        should_skip
    )


def complete_identifier(identifiers=[],
        should_skip=get_active_identifier_skipper()):
    identifier, cursor = get_active_completer().complete_identifier(
        px.buffer.get(),
        px.cursor.get(),
        identifiers,
        should_skip
    )

    if identifier:
        px.cursor.set(cursor)

    return identifier, cursor


def set_active_completer(completer):
    global _ActiveCompleter

    _ActiveCompleter = completer


def get_active_completer():
    if _ActiveCompleter:
        return _ActiveCompleter
    else:
        return wrap_for_filetype('_DefaultCompleter')


def reset_identifier_completion():
    if get_active_completer().should_reset(px.cursor.get()):
        get_active_completer().reset()
        set_active_completer(None)


def highlight_completion():
    identifier = get_active_completer().get_completion()
    if not identifier:
        return

    (line, column) = identifier.position

    return _DefaultHighlighter.highlight(line, column, len(identifier.name))


def clear_highlight():
    return _DefaultHighlighter.clear()


def register_cursor_moved_callback(namespace, target_pos, callback):
    _DefaultCursorMovedCallbackCaller.register(namespace, target_pos, callback)


def free_cursor_moved_callback_namespace(namespace):
    _DefaultCursorMovedCallbackCaller.free_namespace(namespace)


def run_cursor_moved_callbacks():
    _DefaultCursorMovedCallbackCaller.run_callbacks()
