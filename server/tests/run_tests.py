import argparse
import sys
import unittest
import os
import inspect
import re
import importlib.util


class TestView():
    file_path = ''
    class_name = ''
    test_name = ''

    def __init__(self, file_path, class_name, test_name):
        self.file_path = file_path
        self.class_name = class_name
        self.test_name = test_name

    def __str__(self) -> str:
        return re.sub('\\/', '.', self.file_path) + '.' + self.class_name + '.' + self.test_name

def load_module(file_path):
    spec = importlib.util.spec_from_file_location(file_path, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[file_path] = module
    spec.loader.exec_module(module)

def select_test_methods(methods):
    for method in methods[::-1]:
        if not re.fullmatch('test_.*', method):
            methods.remove(method)

def append_tests_from_class(class_obj, list_to_append, module_name):
    methods = dir(class_obj)
    select_test_methods(methods)
    for method in methods:
        list_to_append.append(TestView(module_name[2:-3], class_obj.__name__, method))

def append_tests_from_module(list_to_append, module_name):
    for name, obj in inspect.getmembers(sys.modules[module_name]):
        if inspect.isclass(obj):
            append_tests_from_class(obj, list_to_append, module_name)

def find_all_tests():
    test_files = []
    for path, subdirs, files in os.walk('.'):
        for name in files:
            test_files.append(os.path.join(path, name))

    for file_path in test_files[::-1]:
        if not re.fullmatch('.*test_.*\.py', file_path):
            test_files.remove(file_path)

    tests = []
    for file_path in test_files:
        load_module(file_path)
        append_tests_from_module(tests, file_path)
        del(sys.modules[file_path])

    return tests

def select_tests(tests, regexp, is_exclude):
    if not regexp:
        regexp = '.*'
    select = []
    for test in tests:
        if re.search(regexp, str(test)):
            select.append(not is_exclude)
        else:
            select.append(is_exclude)
    tests = [test for test, is_include in zip(tests, select) if is_include]
    return tests

def run_test(test):
    loader = unittest.TestLoader()
    test_suite = loader.loadTestsFromName(str(test))
    result = unittest.TestResult()
    test_suite.run(result)
    if not result.errors and not result.failures:
        print('Test passed')
        return True
    else:
        print('Test fail!\n')
        if result.failures:
            print(result.failures[0][1])
        else:
            print(result.errors[0][1])
        return False

def print_loop_result(passed, failed):
    if passed:
        i = 1
        print('Following tests passed:')
        for test in passed:
            print('{0})\t{1}'.format(i, test))
            i += 1
        print()
    if failed:
        i = 1
        print('Following tests failed:')
        for test in failed:
            print('{0})\t{1}'.format(i, test))
            i += 1
        print()

def loop_step(current_loop, loop_count, tests):
    passed = []
    failed = []
    for i, test in enumerate(tests):
        print('Loop {0}/{1}\nTest {2}/{3}\t{4}'.format(current_loop, loop_count, i + 1, len(tests), test))
        if run_test(test):
            passed.append(test)
        else:
            failed.append(test)
        print('='*100)
    return passed, failed

#RawTextHelpFormatter support multistring comments
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-N', '--show-only', action='store_true',
                    help='Show tests without running')
parser.add_argument('-R', '--regexp', metavar='EXPRESSION',
                    help='Use tests that satisfy EXPRESSION with python re syntax')
parser.add_argument('-E', '--exclude', action='store_true', default=False,
                    help='Run tests exlude matched')
parser.add_argument('--repeat', metavar='N', default=1,
                    help='Repeat tests run <N> times')

flags = vars(parser.parse_args(sys.argv[1:]))

tests = find_all_tests()

regexp = flags['regexp']
is_exclude = flags['exclude']

tests = select_tests(tests, regexp, is_exclude)

if flags['show_only']:
    i = 1
    for test in tests:
        print('{0})\t{1}'.format(i, test))
        i += 1
else:
    for loop_index in range(int(flags['repeat'])):
        passed, failed = loop_step(loop_index + 1, flags['repeat'], tests)
        print_loop_result(passed, failed)