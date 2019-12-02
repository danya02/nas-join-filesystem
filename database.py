#!/usr/bin/python3

import peewee

db = SqliteDatabase('fs.db')

class MyModel(Model):
    class Meta:
        database = db

class Folder(MyModel):
    parent = ForeignKeyField('self', null=True, backref='child_folders')
    name = CharField(null=False)

class File(MyModel):
    parent_folder = ForeignKeyField(Folder, null=True, backref='child_files')
    name = CharField(null=False)
    length = BigIntegerField(null=False, default=0)
    perms = BitField()
    user_readable = perms.flag()
    user_writeable = perms.flag()
    user_executable = perms.flag()
    group_readable = perms.flag()
    group_writeable = perms.flag()
    group_executable = perms.flag()
    world_readable = perms.flag()
    world_writeable = perms.flag()
    world_executable = perms.flag()
    owner_user = IntegerField(null=False, default=0)
    owner_group = IntegerField(null=False, default=0)

class Disk(MyModel):
    # TODO: store information on how to access disk
    # What common options are there? Local, WebDAV, (S)FTP...?
    path = TextField(null=False)
    length = BigIntegerField(null=False) # set this conservatively, because
                                         # slack space on internal FS and
                                         # disk may also store backup indexes
    backup = BooleanField(default=False) # if true, only backup to this disk


class FileExtent(MyModel):
    file = ForeignKeyField(File, null=False, backref='extents')
    start_offset = BigIntegerField()
    end_offset = BigIntegerField()
    path = TextField(null=False)
    disk = ForeignKeyField(Disk, null=False, backref='extents')

