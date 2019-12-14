#!/usr/bin/python3

from database import *
import exceptions
import file_wrapper

PATH_SEP = '/'

def find_item_by_path(path):
    current_folder = None
    final_item = None
    for path_part in path.split(PATH_SEP):
        if final_item is not None:
            raise exceptions.InvalidPath('There was a path separator after the file "{}" as if it were a folder'.format(final_item.name))
        try:
            current_folder = Folder.get(Folder.name==path_part and Folder.parent==current_folder)
        except Folder.DoesNotExist:
            try:
                final_item = File.get(File.name==path_part and File.parent==current_folder)
            except File.DoesNotExist:
                raise exceptions.ObjectNotFound('File or folder at path {} does not exist').format(path)
    if final_item is None:
        return current_folder
    else:
        return final_item


def create_file(parent_folder, file_name):
    if not isinstance(parent_folder, Folder):
        raise exceptions.NotAFolder
    new_file = File.create(parent_folder=parent_folder, name=file_name, length=0)
    return new_file

def delete_item(item_db_entry):
    if isinstance(item_db_entry, Folder) or isinstance(item_db_entry, File):
        item_db_entry.delete_instance()
    else:
        raise exceptions.NotAnItem

def create_folder(parent_folder, folder_name):
    new_folder = Folder.create(parent=parent_folder, name=folder_name)
    return new_folder

def rename_item(file_db_entry, new_name):
    if PATH_SEP in new_name:
        raise exceptions.InvalidPath('The name must not contain the path separator')
    file_db_entry.name = new_name
    file_db_entry.save()

def move_item(item_db_entry, new_parent):
    if isinstance(new_parent, Folder) or new_parent is None:
        if isinstance(item_db_entry, Folder) or isinstance(item_db_entry, File):
            item_db_entry.parent = new_parent
            item_db_entry.save()
        else:
            raise exceptions.NotAnItem
    else:
        raise exceptions.NotAFile

def open_file(file_db_object, mode='r'):
    if not isinstance(file_db_object):
        raise exceptions.NotAFile
    return file_wrapper.File(file_db_object, is_readable='r' in mode, is_writable='w' in mode)
