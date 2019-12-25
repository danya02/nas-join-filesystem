#!/usr/bin/python3

from abc import ABC, abstractmethod
import io

def open(extent, mode):
    """
    Open a file-like object to reference an extent.

    Supported modes are "r" for read, "w" for write.
    """

    path = extent.disk.path+extent.path
    scheme, _, path = path.partition('://')
    if scheme=='file':
        return LocalFileExtentHandle(path, mode)
    else:
        raise ValueError('Unknown URI scheme: '+scheme)

def range_intersect(x, y):
    """
    Convinience function that returns the intersection of two
    range()s (or other items that represent ranges that have a 0th and
    a -1th element).
 
    Useful for checking extent intersection while write()ing.

    From https://stackoverflow.com/a/6821298
    """
    return range(max(x[0], y[0]), min(x[-1], y[-1])+1)

class ExtentFileHandle(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def read(self, start_offset, size=1):
        """
        Read this many bytes from start_offset.
        
        If it is infeasible to read the given number of bytes, it is
        permitted to read more than the specified number, however
        the method must return exactly as many bytes as requested.

        If the number of bytes exceeds the available range from the current
        offset, the returned object must have all the bytes remaining in
        the available range.

        If this is opened as write-only, this should raise an io.UnsupportedOperation.
        """
        pass

    @abstractmethod
    def write(self, data, start_offset):
        """
        Write these bytes at start_offset.
        Return the number of bytes actually written.

        data must be a sliceable object returning bytes-like objects.

        If the range of bytes to write intersects the extent partially, write the intersection.
        If the range is entirely outside of the bounds of this extent, do not do anything.
        This is so that there is no bounds checking in calling code.

        If this is opened as read-only, this should raise a io.UnsupportedOperation.
        """
        pass

    @abstractmethod
    def close(self):
        """Close this file handle."""
        pass

    def __del__(self):
        self.close()

class LocalFileExtentHandle(ExtentFileHandle):
    """File handle to an extent on the local filesystem."""

    def __init__(self, extent, path, mode):
        self.fd = open(path, mode+'b')
        self.mode = mode
        self.extent = extent


    def read(self, start_offset, size=1):
        if mode!='r':
            raise io.UnsupportedOperation('not readable')
        if start_offset-self.extent.start_offset in self.extent.range:
            self.fd.seek(start_offset-self.extent.start_offset)
            return self.fd.read(size)
        except:
            return b''

    def write(self, data, start_offset):
        if mode!='w':
            raise io.UnsupportedOperation('not writeable')
        data_range = range(start_offset, len(data)+start_offset)
        write_range = range_intersection(self.extent.range, data_range)
        bytes_offset = write_range[0]-start_offset
        bytes_count = len(write_range)
        self.fd.seek(write_range[0])
        self.fd.write(data[bytes_offset:bytes_offset+bytes_count])

    def close(self):
        self.fd.close()

