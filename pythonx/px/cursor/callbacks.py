# coding=utf8

import vim

import px.cursor

class MovedCallbackCaller(object):

    def __init__(self):
        self._callbacks = {}

    def register(self, namespace, target_pos, callback):
        if namespace not in self._callbacks:
            self._callbacks[namespace] = []

        self._callbacks[namespace].append((target_pos, callback))

    def run_callbacks(self):
        current_pos = px.cursor.get_adjusted()

        new_callbacks = {}
        for namespace, callbacks in self._callbacks.items():
            left = []
            found = False
            for target_pos, callback in callbacks:
                if current_pos == target_pos and not found:
                    found = True

                    callback()
                else:
                    left.append((target_pos, callback))

            if left:
                new_callbacks[namespace] = left

        self._callbacks = new_callbacks

    def free_namespace(self, namespace):
        del self._callbacks[namespace]
