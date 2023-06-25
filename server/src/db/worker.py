import sqlite3
import json
import os
import sys

from .. import config

def update_entry(db, table_name, id_name, id_value, field_name, field_value):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    if type(field_value) == list:
        string_value = ''
        for value in field_value:
            string_value += config.DELIMITER + str(value) + config.DELIMITER
        field_value = string_value
    update = "UPDATE {0} SET {1} = '{2}' WHERE {3} = {4}".format(table_name,
                                                                 field_name,
                                                                 field_value,
                                                                 id_name,
                                                                 id_value)
    
    cursor.execute(update)
    connection.commit()
    connection.close()

def add_entry(db, table_name, id_name, data):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()

    '''
    select return info about all column in %TABLE_NAME%:
    'id' (number of column in result)
    'name' (its name); 
    'type' (data type if given, else ''); 
    'notnull' (whether or not the column can be NULL); 
    'dflt_value' (the default value for the column);
    'pk' (either zero for columns that are not part of the primary key, 
          or the 1-based index of the column within the primary key)
    '''
    columns = cursor.execute("SELECT * FROM pragma_table_info('{0}')".format(table_name))
    columns = columns.fetchall()

    required_columns = [column_info[1] for column_info in columns if column_info[3]]
    required_column_names = ''
    for column_name in required_columns:
        required_column_names += column_name + ', '
    required_column_names = required_column_names[:-2]

    required_columns_values = ''
    for column_name in required_columns:
        required_columns_values += '"' + str(data[column_name]) + '", '
    required_columns_values = required_columns_values[:-2]
    insert = 'INSERT INTO {0} ({1}) VALUES ({2})'.format(table_name, required_column_names,
                                                        required_columns_values)

    cursor.execute(insert)
    connection.commit()
    id = cursor.lastrowid

    nonrequired_columns = [column_info[1] for column_info in columns if not column_info[3]]
    for column_name in nonrequired_columns:
        if column_name in data.keys():
            update_entry(db,
                         table_name,
                         id_name,
                         id,
                         column_name, 
                         data[column_name])
    connection.close()
    return {'id': id}

def add_exclude_select_part(exclude):
    additional_part = ''
    for field_name in exclude.keys():
        additional_part += '{0} NOT LIKE'.format(field_name)
        for field_value in exclude[field_name]:
            additional_part += ' {0} AND NOT LIKE'.format(field_value)
        additional_part = additional_part[:-8]
    additional_part = additional_part[:-5]
    return additional_part

def create_select_request(requested_fields_name, table_name, id_name=None, id_value=None, exclude=None):
    request = 'SELECT {0} FROM {1}'.format(requested_fields_name, table_name)

    if not id_value and not exclude:
        return request

    request += ' WHERE '
    if id_value:
        request += '{0} = {1} AND'.format(id_name, id_value)
    if exclude:
        request += add_exclude_select_part(exclude)
    else:
        request = request[:-4]
    return request

def get_entry_data(db, table_name, fields_name, id_name=None, id_value=None, exclude=None):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()

    requested_fields_name = ''
    for field_name in fields_name:
        requested_fields_name += field_name + ', '
    requested_fields_name = requested_fields_name[:-2]

    select = create_select_request(requested_fields_name, table_name, id_name, id_value, exclude)
    select = cursor.execute(select)
    select = select.fetchall()
    connection.close()

    if len(select) == 0:
        return

    if len(select) == 1:
        select = select[0]
        requested_data = {}
        for i, value in enumerate(select):
            requested_data[fields_name[i]] = value
    else:
        requested_data = {}
        for i, field_name in enumerate(fields_name):
            requested_data[field_name] = [row[i] for row in select]

    return requested_data