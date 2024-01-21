'''
В этом файле собраны функции и классы, которые используется сервером при обработке входящих запросов.
Так в этом файле хрянятся функции по предобработке заголовоков входящих запросов, которые посылаются в строковом виде.
'''

import json
from .. import request_status

class Parameter():
    def __init__(self, name:str, parameter_type:str, is_required:bool):
        self.name = name
        self.type = parameter_type
        self.is_required = is_required

def safe_parser(func):
    def wrapper(**kwargs):
        try:
            headers = func(**kwargs)
        except ValueError as err:
            return request_status.Status(request_status.StatusType.ERROR,
                                         error_type=request_status.ErrorType.ValueError,
                                         msg=f"Cannot convert {kwargs['parameter_name']} or value is forbidden"), None
        return request_status.Status(request_status.StatusType.OK), headers
    return wrapper

@safe_parser
def parse_int(**kwargs):
    return int(kwargs['headers'].get(kwargs['parameter_name']))

@safe_parser
def parse_list_of_int(**kwargs):
    indexes = str(kwargs['headers'].get(kwargs['parameter_name']))
    indexes = indexes.split('~')[1:-1]
    indexes = [int(index) for index in indexes]
    if not indexes:
        raise ValueError(f'Value is None: {indexes}')
    return indexes

@safe_parser
def parse_json(**kwargs):
    result = kwargs['headers'].get(kwargs['parameter_name'])
    if type(result) is dict:
        return result
    return json.loads(result)

@safe_parser
def parse_str(**kwargs):
    # possible errors converted to string
    forbidden_values = ['none', 'nan', 'null', '']
    result = str(kwargs['headers'].get(kwargs['parameter_name']))
    if result.lower() in forbidden_values:
        raise ValueError(f'Cannot convert {result} to string format')
    return result

@safe_parser
def parse_list(**kwargs):
    # [], {}, \"\", \'\' converted to str
    forbidden_values = ['"', "'", '[', '{']
    result = str(kwargs['headers'].get(kwargs['parameter_name']))
    result = result.split('~')[1:-1]
    if not result or result[0] in forbidden_values:
        raise ValueError(f'Cannot convert {result} to list format')
    return result

@safe_parser
def parse_bool(**kwargs):
    true_values = ['true', 'y', '1']
    false_values = ['false', 'n', '0']
    result = str(kwargs['headers'].get(kwargs['parameter_name']))
    if result.lower() in true_values:
        return True
    elif result.lower() in false_values:
        return False
    else:
        raise ValueError(f'Cannot convert {result} to bool format')

@safe_parser
def parse_date(**kwargs):
    result = kwargs['headers'].get(kwargs['parameter_name'])
    result = result.split('-')
    if len(result) != 3:
        raise ValueError(f'Cannot convert {result} to date format')
    day = int(result[0])
    month = int(result[1])
    year = int(result[2])
    return [day, month, year]


def parse_fields(request_part, structure:list):
    skipped = ''
    fields = []
    for parameter in structure:
        parameter:Parameter
        if parameter.name not in request_part:
            skipped += parameter.name + ', '
        else:
            fields.append(parameter.name)
    if not fields:
        skipped = skipped[:-2]
        return request_status.Status(request_status.StatusType.ERROR,
                                     request_status.ErrorType.OptionError,
                                     msg = f'Request doesnt have any of ({skipped}) headers'), None
    return request_status.Status(request_status.StatusType.OK), fields

def parse_structure(request_part:dict, structure:list):
    result = {}
    requested_headers = ''
    parameter:Parameter
    for parameter in structure:
        if parameter.name not in request_part and parameter.is_required:
            return request_status.Status(request_status.StatusType.ERROR,
                                         request_status.ErrorType.OptionError,
                                         msg = f'Missed required key {parameter.name}'), None
        if parameter.name not in request_part:
            requested_headers += parameter.name + ', '
            continue
        status:request_status.Status
        status = None
        value = None
        match parameter.type:
            case 'int':
                status, value = parse_int(headers=request_part,
                                          parameter_name=parameter.name)
            case 'list_of_int':
                status, value = parse_list_of_int(headers=request_part,
                                                  parameter_name=parameter.name)
            case 'json':
                status, value = parse_json(headers=request_part,
                                           parameter_name=parameter.name)
            case 'str':
                status, value = parse_str(headers=request_part,
                                          parameter_name=parameter.name)
            case 'list':
                status, value = parse_list(headers=request_part,
                                           parameter_name=parameter.name)
            case 'bool':
                status, value = parse_bool(headers=request_part,
                                            parameter_name=parameter.name)
            case 'date':
                status, value = parse_date(headers=request_part,
                                           parameter_name=parameter.name)

        if status.is_error:
            return status, None
        result[parameter.name] = value

    if not result:
        requested_headers = requested_headers[:-2]
        return request_status.Status(request_status.StatusType.ERROR,
                                     request_status.ErrorType.OptionError,
                                     msg = f'Request doesnt have any of ({requested_headers}) headers'), None

    return request_status.Status(request_status.StatusType.OK), result
