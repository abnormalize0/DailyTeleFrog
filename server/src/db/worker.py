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
        is_id_exist = cursor.execute(f'SELECT * from {table_name} WHERE {id_name} = {id_value}')
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
        string_value = ''
        for value in field_value:
            string_value += config.DELIMITER + str(value) + config.DELIMITER
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

def add_exclude_select_part(exclude):
    additional_part = ''
    for field_name in exclude.keys():
        additional_part += f'{field_name} NOT LIKE'
        for field_value in exclude[field_name]:
            additional_part += f' {field_value} AND NOT LIKE'
        additional_part = additional_part[:-8]
    additional_part = additional_part[:-5]
    return additional_part

def create_select_request(requested_fields_name, table_name, id_name=None, id_value=None, exclude=None):
    request = f'SELECT {requested_fields_name} FROM {table_name}'

    if not id_value and not exclude:
        return request

    request += ' WHERE '
    if id_value:
        request += f'{id_name} = {id_value} AND'
    if exclude:
        request += add_exclude_select_part(exclude)
    else:
        request = request[:-4]
    return request

@log.log_args_kwargs(config.log_db_api)
@log.timer(config.log_db_api)
def get_entry_data(db, table_name, fields_name, id_name=None, id_value=None, exclude=None):
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

    select = create_select_request(requested_fields_name, table_name, id_name, id_value, exclude)
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