import sqlite3

from .. import config
from .. import request_status

def is_field_exist(db, table_name, id_name=None, id_value=None, field_name=None):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    is_id_exist = True
    if id_name:
        is_id_exist = cursor.execute('SELECT * from {0} WHERE {1} = {2}'.format(table_name,
                                                                                id_name,
                                                                                id_value))
        is_id_exist = is_id_exist.fetchall()
    if not is_id_exist:
        connection.close()
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.ValueError,
                                     msg='table {0} in db {1} does not have entry with id = {2}'.format(table_name,
                                                                                                        db,
                                                                                                        id_value))

    if not field_name:
        connection.close()
        return request_status.Status(request_status.StatusType.OK)

    columns = cursor.execute("SELECT * FROM pragma_table_info('{0}')".format(table_name))
    columns = columns.fetchall()
    columns = [column_info[1] for column_info in columns]
    connection.close()
    if not field_name in columns:
        return request_status.Status(request_status.StatusType.ERROR,
                                     error_type=request_status.ErrorType.OptionError,
                                     msg='table {0} in db {1} does not have field with name {2}'.format(table_name,
                                                                                                        db,
                                                                                                        field_name))

    return request_status.Status(request_status.StatusType.OK)

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
    update = "UPDATE {0} SET {1} = '{2}' WHERE {3} = {4}".format(table_name,
                                                                 field_name,
                                                                 field_value,
                                                                 id_name,
                                                                 id_value)
    cursor.execute(update)
    connection.commit()
    connection.close()
    return request_status.Status(request_status.StatusType.OK)

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
    columns = cursor.execute("SELECT * FROM pragma_table_info('{0}')".format(table_name))
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
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.OptionError,
                                         msg='Cannot find value for field {0} in table {1} in database {2}'.format(
                                            column_name,
                                            table_name,
                                            db
                                         )), None

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
                                         msg='Unknown field {0} in table {1} in database {2}'.format(
                                            column_name,
                                            table_name,
                                            db
                                         )), None
        if column_name in required_column_names:
            continue

        try:
            nonrequired_columns_values += '"' + str(data[column_name]) + '", '
            nonrequired_column_names += str(column_name) + ', '
        except:
            connection.close()
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.OptionError,
                                         msg='Cannot find value for field {0} in table {1} in database {2}'.format(
                                            column_name,
                                            table_name,
                                            db
                                         )), None

    if not nonrequired_column_names:
        insert_columns_values = required_columns_values[:-2]
        insert_column_names = required_column_names[:-2]
    else:
        insert_columns_values = required_columns_values + nonrequired_columns_values[:-2]
        insert_column_names = required_column_names + nonrequired_column_names[:-2]

    insert = 'INSERT INTO {0} ({1}) VALUES ({2})'.format(table_name, insert_column_names,
                                                        insert_columns_values)
    cursor.execute(insert)
    connection.commit()
    id = cursor.lastrowid
    connection.close()
    return request_status.Status(request_status.StatusType.OK), id

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