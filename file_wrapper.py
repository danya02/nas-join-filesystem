#!/usr/bin/python3

from database import *
import exceptions
import io
import itertools
import file_handles


class LazyExtentOpener:
    """
    A dict-like object that opens file handles to extents lazily.

    When an item identified by an Extent object is requested,
    its id property is read. If an object with this id was previously
    requested, the opened file handle is returned. Otherwise, the object
    is used to instantiate a file handle.

    The passed key must always have a `obj.id` property, which
    is usually an integer. In general, this is guaranteed to work
    with Extent instances from `database.py`.
    """
    def __init__(self, mode):
        self.extents = dict()
        self.mode = mode

    def __contains__(self, key):
        return key.id in self.extents

    def __delitem__(self, key):
        del self.extents[key.id]

    def __len__(self):
        return len(self.extents)

    def __getitem__(self, key):
        """
        Get a file handle to given extent.

        May raise exceptions if there were errors while opening the extent
        or if the data for the extent is invalid.
        """
        if key.id in self.extents:
            return self.extents[key.id]
        else:
            fd = file_handles.open(key, mode)
            self.extents[key.id] = fd
            return fd

    def open_many(self, to_open):
        """
        Instantiate multiple file handles for extents in the given list.

        May be useful if open errors are to be detected early.
        """
        for i in self.to_open:
            self[i]

    def __del__(self):
        self.close_all()

    def close_all(self):
        """Close all opened file handles."""
        for i in self.extents:
            i.close()

class File(io.IOBase):
    """An object to access the binary contents of a File in the filesystem."""
    def __init__(self, file_db_object, is_readable=True, is_writable=False):
        self.fd = file_db_object
        self.cursor = 0
        self.is_read = is_readable
        self.is_write = is_writable
        if self.is_read and self.is_write:
            raise exceptions.APIError('A file cannot be opened as both readable and writable')
            # TODO: is it possible to make this work without this limitation?
            # Is it even useful?

        self.extents = list(FileExtent.select(FileExtent, Disk)
            .where(FileExtent.file == self.fd).join(Disk))
        self.extents.sort(key=lambda x: (x.disk.read_priority,
                -len(range(x.start_offset, x.end_offset)),
                x.start_offset)
                )
        self.extent_opener = LazyExtentOpener('r' if self.is_read else 'w' if self.is_write else '?')

    def close(self):
        self.extent_opener.close_all()

    def fileno(self):
        raise self.fd.id

    def flush(self):
        pass # might add some buffering in the future?

    def isatty(self):
        return False

    def seekable(self):
        return True

    def seek(self, offset, whence=0):
        if whence==0: # SEEK_SET, relative to beginning
            self.cursor = offset
        elif whence==1: # SEEK_CUR, relative to cursor
            self.cursor += offset
        elif whence==2: # SEEK_END, relative to end
            self.cursor = self.fd.length - offset

    def tell(self):
        return self.cursor

    def readable(self):
        return self.is_read

    def writable(self):
        return self.is_write

    def read(self, size=-1):
        arr_cursor = 0
        if size>-1:
            arr = bytearray(min(size, len(range(self.cursor, self.fd.length))))
        else:
            arr = bytearray(len(range(self.cursor, self.fd.length)))
        while arr_cursor != len(arr):
            for extent in self.extents:
                while self.cursor in extent.range:
                    arr[arr_cursor] = self.extent_opener.read(arr_cursor, 1)
                    arr_cursor += 1
                    self.cursor += 1
                    if arr_cursor >= len(arr):
                        return bytes(arr)
        return bytes(arr)

    def readinto(self, buffer):
        raise NotImplementedError # FIXME: move code from read()

    def readall(self):
        return self.read()

    def truncate(self):
        raise NotImplementedError # FIXME: create algorithm for (de)allocating extents

    def write(self, buffer): # TODO: seems like this implementation is not very optimal -- check?
        if self.cursor + len(buffer) >= self.fd.length:
            self.truncate(self.cursor + len(buffer))
        for extent in self.extents:
            self.extent_opener[extent].write(buffer, self.cursor)            

        self.cursor += len(buffer)
        return len(buffer)
