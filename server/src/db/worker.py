'''
Этот файл служит для формирования запросов к базам данных и их выполнение.
'''

import sqlite3

from .. import config
from .. import log
from .. import request_status

def is_field_exist(db, table_name, id_name=None, id_value=None, field_name=None):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    is_id_exist = True
    if id_name:
        import sys
        select = f"SELECT * from {table_name} WHERE {id_name} = '{id_value}'"
        is_id_exist = cursor.execute(select)
        is_id_exist = is_id_exist.fetchall()
    if not is_id_exist:
        connection.close()
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg=f'table {table_name} in db {db} does not have entry with id = {id_value}')

    if not field_name:
        connection.close()
        return request_status.Status(request_status.StatusType.OK)

    columns = cursor.execute(f"SELECT * FROM pragma_table_info('{table_name}')")
    columns = columns.fetchall()
    columns = [column_info[1] for column_info in columns]
    connection.close()
    if not field_name in columns:
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.OptionError,
                                     msg=f'table {table_name} in db {db} does not have field with name {field_name}')

    return request_status.Status(request_status.StatusType.OK)

@log.log_args_kwargs(config.log_db_api)
@log.timer(config.log_db_api)
def update_entry(db, table_name, id_name, id_value, field_name, field_value):
    status = is_field_exist(db, table_name, id_name, id_value)
    if status.is_error:
        return status

    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    if type(field_value) == list:
        string_value = config.delimiter
        for value in field_value:
            string_value += str(value) + config.delimiter
        field_value = string_value
    update = f"UPDATE {table_name} SET {field_name} = '{field_value}' WHERE {id_name} = {id_value}"
    cursor.execute(update)
    connection.commit()
    connection.close()
    return request_status.Status(request_status.StatusType.OK)

@log.log_args_kwargs(config.log_db_api)
@log.timer(config.log_db_api)
def add_entry(db, table_name, data):
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
    columns = cursor.execute(f"SELECT * FROM pragma_table_info('{table_name}')")
    columns = columns.fetchall()

    required_columns = [column_info[1] for column_info in columns if column_info[3]]
    required_column_names = ''
    for column_name in required_columns:
        required_column_names += column_name + ', '

    required_columns_values = ''
    for column_name in required_columns:
        try:
            if type(data[column_name]) == list:
                string_value = config.delimiter
                for value in data[column_name]:
                    string_value += str(value) + config.delimiter
                data[column_name] = string_value
            required_columns_values += '"' + str(data[column_name]) + '", '
        except:
            connection.close()
            message = f'Cannot find value for field {column_name} in table {table_name} in database {db}'
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.OptionError,
                                         msg=message), None

    nonrequired_columns = [column_info[1] for column_info in columns if not column_info[3]]
    possible_nonrequired_column_names = ''
    for column_name in nonrequired_columns:
        possible_nonrequired_column_names += column_name + ', '

    nonrequired_columns_values = ''
    nonrequired_column_names = ''
    for column_name in data.keys():
        if column_name not in possible_nonrequired_column_names and column_name not in required_column_names:
            connection.close()
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.OptionError,
                                         msg=f'Unknown field {column_name} in table {table_name} in database {db}'
                                        ), None
        if column_name in required_column_names:
            continue

        try:
            if type(data[column_name]) == list:
                string_value = config.delimiter
                for value in data[column_name]:
                    string_value += str(value) + config.delimiter
                data[column_name] = string_value
            nonrequired_columns_values += '"' + str(data[column_name]) + '", '
            nonrequired_column_names += str(column_name) + ', '
        except:
            connection.close()
            message = f'Cannot find value for field {column_name} in table {table_name} in database {db}'
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.OptionError,
                                         msg=message), None

    if not nonrequired_column_names:
        insert_columns_values = required_columns_values[:-2]
        insert_column_names = required_column_names[:-2]
    else:
        insert_columns_values = required_columns_values + nonrequired_columns_values[:-2]
        insert_column_names = required_column_names + nonrequired_column_names[:-2]

    insert = f'INSERT INTO {table_name} ({insert_column_names}) VALUES ({insert_columns_values})'
    cursor.execute(insert)
    connection.commit()
    id = cursor.lastrowid
    connection.close()
    return request_status.Status(request_status.StatusType.OK), id

def add_include_select_part(include:dict):
    additional_part = ''
    left = ''
    right = ''
    for field_name in include.keys():
        additional_part += f''
        if field_name == 'tags':
            left = '%~'
            right = '~%'
        else:
            left = ''
            right = ''
        for field_value in include[field_name]:
            additional_part += f"{field_name} LIKE '{left}{field_value}{right}' AND "
    additional_part = additional_part[:-5]
    return additional_part

def add_exclude_select_part(exclude:dict):
    additional_part = ''
    left = ''
    right = ''
    for field_name in exclude.keys():
        if field_name == 'tags':
            left = '%~'
            right = '~%'
        else:
            left = ''
            right = ''
        for field_value in exclude[field_name]:
            additional_part += f"{field_name} NOT LIKE '{left}{field_value}{right}' AND "
    additional_part = additional_part[:-5]
    return additional_part

def add_bounds_select_part(bounds):
    additional_part = ''
    if 'upper-date' in bounds.keys():
        additional_part += f'creation_date < {bounds["upper-date"]} AND '
    if 'lower-date' in bounds.keys():
        additional_part += f'creation_date > {bounds["lower-date"]} AND '
    if 'upper-rating' in bounds.keys():
        additional_part += f'rating < {bounds["upper-rating"]} AND '
    if 'lower-rating' in bounds.keys():
        additional_part += f'rating > {bounds["lower-rating"]} AND '
    additional_part = additional_part[:-5]
    return additional_part

def add_sort(sort_column, sort_direction):
    if sort_direction == 'ascending':
        return f'ORDER BY {sort_column} ASC'
    else:
        return f'ORDER BY {sort_column} DESC'

def remove_nonsub_from_select(id):
    connection = sqlite3.connect(config.db_user.path)
    cursor = connection.cursor()

    _ = f'SELECT sub_tags, sub_users, sub_communities from {config.user_table_name} WHERE {config.user_id_name} = {id}'
    select = cursor.execute(_)
    select = select.fetchall()
    connection.close()

    sub_tag = select[0][0]
    sub_user = select[0][1]
    sub_community = select[0][2]

    additional_part = ''
    if sub_tag or sub_user or sub_community:
        if sub_tag:
            for tag in sub_tag.split('~')[1:-1]:
                additional_part += f"tags LIKE '%~{tag}~%' OR "
        if sub_user:
            for user in sub_user.split('~')[1:-1]:
                additional_part += f"author_id LIKE '%~{user}~%' OR "
        if sub_community:
            for community in sub_community.split('~')[1:-1]:
                additional_part += f"community LIKE '%~{community}~%' OR "
        additional_part = additional_part[:-4]

    return additional_part

def create_select_request(requested_fields_name, table_name,
                          id_name=None, id_value=None, include_nonsub=None, include=None, exclude=None,
                          bounds=None, sort_column=None, sort_direction=None, user_id=None):
    request = f'SELECT {requested_fields_name} FROM {table_name}'

    if id_value or include or exclude or bounds or not include_nonsub:
        request += ' WHERE '
        if id_value:
            request += f"{id_name} = '{id_value}' AND "
        if include:
            request += add_include_select_part(include) + ' AND '
        if exclude:
            request += add_exclude_select_part(exclude) + ' AND '
        if bounds:
            request += add_bounds_select_part(bounds) + ' AND '
        if include_nonsub is not None and not include_nonsub:
            request += remove_nonsub_from_select(user_id) + ' AND '
        request = request[:-5]
    if sort_column and sort_direction:
        request += ' ' + add_sort(sort_column, sort_direction)
    return request

@log.log_args_kwargs(config.log_db_api)
@log.timer(config.log_db_api)
def get_entry_data(db, table_name, fields_name,
                   id_name=None, id_value=None, include=None, exclude=None,
                   include_nonsub=None, bounds=None, sort_column=None, sort_direction=None, user_id=None):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()

    requested_fields_name = ''
    for field_name in fields_name:
        status = is_field_exist(db, table_name, id_name=id_name, id_value=id_value, field_name=field_name)
        if status.is_error:
            connection.close()
            return status, None
        requested_fields_name += field_name + ', '
    requested_fields_name = requested_fields_name[:-2]

    select = create_select_request(requested_fields_name,
                                   table_name,
                                   id_name,
                                   id_value,
                                   include_nonsub,
                                   include,
                                   exclude,
                                   bounds,
                                   sort_column,
                                   sort_direction,
                                   user_id)
    select = cursor.execute(select)
    select = select.fetchall()
    connection.close()

    if len(select) == 0:
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg='Empty data for select request'), None

    if len(select) == 1:
        select = select[0]
        requested_data = {}
        for i, value in enumerate(select):
            requested_data[fields_name[i]] = value
    else:
        requested_data = {}
        for i, field_name in enumerate(fields_name):
            requested_data[field_name] = [row[i] for row in select]
    return request_status.Status(request_status.StatusType.OK), requested_data