#!/usr/bin/python3

from database import *
import exceptions
import io
import itertools

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

        self.extents = sorted(list(FileExtent.select(FileExtent, Disk)
            .where(FileExtent.file == self.fd).join(Disk)),
            key=lambda x: (x.disk.read_priority,
                -len(range(x.start_offset, x.end_offset)),
                x.start_offset))

    def close(self):
        pass # there isn't much to close atm. maybe have persistent file handles for extents?

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
                    arr[arr_cursor] = 0xff
                    arr_cursor += 1
                    self.cursor += 1
                    if arr_cursor >= len(arr):
                        return bytes(arr)
                    raise NotImplementedError # FIXME: add real method for reading data in extent
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
            if self.cursor in extent.range:
                if len(range(self.cursor, self.end_offset)) >= len(buffer): # if the buffer fits entirely into this extent
                    crop_buffer = len(buffer)
                else: # if the entire buffer cannot be written into this extent
                    crop_buffer = len(range(self.cursor, self.end_offset))
                for byte in itertools.islice(buffer, crop_buffer):

                    raise NotImplementedError # FIXME: add real method for writing data to extent
                    
        self.cursor += len(buffer)
        return len(buffer)
