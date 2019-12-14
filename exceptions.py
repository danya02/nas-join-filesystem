#!/usr/bin/python3

class FilesystemException(Exception):
    """Base class for all exceptions relating to the join filesystem."""

class APIError(FilesystemError):
    """Errors relating to invalid usage of the API by consumers."""

class IncorrectArgumentType(APIError, TypeError):
    """The supplied argument does not have the correct type."""
    def __init__(self, *args, **kwargs):
        super(APIError).__init__(self, *args, **kwargs)

class NotAnItem(IncorrectArgumentType):
    """The supplied object is not a filesystem item."""

class NotAFile(NotAnItem):
    """The supplied object is not a File."""

class NotAFolder(NotAnItem):
    """The supplied object is not a Folder."""

class PathError(FilesystemException):
    """Errors relating to paths."""

class ObjectNotFound(PathError):
    """No object with this path was found."""

class InvalidPath(PathError):
    """The path given was not valid for some reason."""
