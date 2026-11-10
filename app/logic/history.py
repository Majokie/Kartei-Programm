"""History for undo / redo in the card editor.

After every completed step (stroke drawn, text edited, moved, inserted,
deleted, ...) the history remembers a copy of the card.
Everything is kept in memory only and applies to the card currently shown.
Switching cards or closing the editor discards the history.
No Qt, no files -> testable with pytest.
"""
import copy

DEFAULT_LIMIT = 10   # number of steps you can go back


class History:
    def __init__(self, limit: int = DEFAULT_LIMIT):
        self.limit = limit
        self._undo: list = []   # older states
        self._redo: list = []   # undone states
        self._current = None    # state after the last step

    def reset(self, state) -> None:
        """New starting point (e.g. another card loaded), clear the history"""
        self._undo.clear()
        self._redo.clear()
        self._current = copy.deepcopy(state)

    def record(self, state) -> bool:
        """Remember a completed step. If nothing changed, nothing happens.
        Returns True if a step was actually recorded."""
        if state == self._current:
            return False
        self._undo.append(self._current)
        if len(self._undo) > self.limit:
            self._undo.pop(0)          # forget the oldest step
        self._current = copy.deepcopy(state)
        self._redo.clear()             # after a new change there is nothing left to redo
        return True

    def undo(self):
        """Returns the previous state (as a copy) or None"""
        if not self._undo:
            return None
        self._redo.append(self._current)
        self._current = self._undo.pop()
        return copy.deepcopy(self._current)

    def redo(self):
        """Returns the undone state (as a copy) or None"""
        if not self._redo:
            return None
        self._undo.append(self._current)
        self._current = self._redo.pop()
        return copy.deepcopy(self._current)

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)
