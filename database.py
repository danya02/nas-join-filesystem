#!/usr/bin/python3

import peewee

db = SqliteDatabase('fs.db', pragmas={'foreign_keys':1})

class MyModel(Model):
    class Meta:
        database = db

class Folder(MyModel):
    parent = ForeignKeyField('self', null=True, backref='child_folders', on_delete='CASCADE')
    name = CharField(null=False)

class File(MyModel):
    parent = ForeignKeyField(Folder, null=True, backref='child_files', on_delete='CASCADE')
    name = CharField(null=False)
    length = BigIntegerField(null=False, default=0)

class Disk(MyModel):
    # TODO: store information on how to access disk
    # What common options are there? Local, WebDAV, (S)FTP...?
    
    # Where can we even store this? Perhaps in the URI schema of the path?
    path = TextField(null=False)
    length = BigIntegerField(null=False) # set this conservatively, because
                                         # slack space on internal FS and
                                         # disk may also store backup indexes
    backup = BooleanField(default=False) # if true, only backup to this disk
    read_priority = IntegerField(default=100000) # if this is low, it is likely that
                                   # this disk will be selected to read from when
                                   # multiple file extents overlap a byte.


class FileExtent(MyModel):
    file = ForeignKeyField(File, null=False, backref='extents', on_delete='CASCADE')
    start_offset = BigIntegerField() # This extent has file's bytes from here
    end_offset = BigIntegerField()   # to here (first incl, last excl)
    path = TextField(null=False)
    disk = ForeignKeyField(Disk, null=False, backref='extents', on_delete='CASCADE')

    def __len__(self):
        return len(self.range)

    @property
    def range(self):
        return range(self.start_offset, self.end_offset)
