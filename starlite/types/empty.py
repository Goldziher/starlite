from typing import Type

__all__ = ("Empty",)


class Empty:
    """A sentinel class used as placeholder."""


EmptyType = Type[Empty]
