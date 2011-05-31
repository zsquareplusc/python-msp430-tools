#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Parse algebraic expressions (infix) and output postfix notation.
"""

import re

class Scanner(object):

    scannerRE = re.compile(r'''
       (?P<SPACE>           \s+             ) |
       (?P<LEFT>            \(              ) |
       (?P<RIGHT>           \)              ) |
       (?P<HEXNUMBER>       0x[0-9a-f]+     ) |
       (?P<BINNUMBER>       0b[01]+         ) |
       (?P<NUMBER>          \d+             ) |
       (?P<UNARYOPERATOR>   not|(\B[-+~]\b)   ) |
       (?P<OPERATOR>        or|and|<<|>>|==|!=|<=|>=|[-+*/\|&\^<>] ) |
       (?P<VARIABLE>        \.?[$_a-z]\w*   )
    ''', re.VERBOSE|re.IGNORECASE|re.UNICODE)

    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.len = len(source)

    def scan(self):
        while True:
            if self.pos >= self.len:
                return None, None
            m = self.scannerRE.match(self.source, self.pos)
            if m is None:
                raise ValueError('invalid token: %r...' % (self.source[self.pos:self.pos+10],))
            self.pos = m.end()
            token_type = m.lastgroup
            if token_type != 'SPACE':
                token = m.group(token_type)
                if token_type == 'HEXNUMBER':
                    token = int(token, 16)
                    token_type = 'NUMBER'
                elif token_type == 'BINNUMBER':
                    token = int(token[2:], 2)
                    token_type = 'NUMBER'
                elif token_type == 'NUMBER':
                    token = int(token)
                elif token_type == 'UNARYOPERATOR':
                    if token == '-': token = 'neg'
                    elif token == '+': token = '0 +'
                return token_type, token

default_precedence_list = [
        # lowest precedence
        ['or'],
        ['and'],
        ['not'],
        ['<', '<=', '>', '>=', '==', '!='],
        ['|', '^', '&'],
        ['<<', '>>'],
        ['+', '-'],
        ['*', '/', '%'],
        ['~', 'neg', '0 +'],
        ['(', ')'],
        # highest precedence
        ]

def convert_precedence_list(precedence_list):
    precedence = {}
    for priority, equals in enumerate(precedence_list):
        for operator in equals:
            precedence[operator] = priority
    return precedence

default_precedence = convert_precedence_list(default_precedence_list)

def print_precedence_list():
    print "Operator precedence from lowest to highest:"
    for priority, equals in enumerate(precedence_list):
        print '%d: %s' % (priority, ' '.join(equals))

#~ print_precedence_list()


def infix2postfix(expression, variable_prefix='', scanner=Scanner, precedence=default_precedence):
    """\
    Convert an expression to postfix notation (RPN), respecting parentheses and
    operator precedences.

    >>> infix2postfix(u'1+2')
    u'1 2 +'
    >>> infix2postfix(u'1+ 2')
    u'1 2 +'

    # >>> infix2postfix(u'1 +2') # interpreted as unary plus, OK
    # u'1 2 +

    >>> infix2postfix(u'1 + 2')
    u'1 2 +'
    >>> infix2postfix(u'1+2*3')
    u'1 2 3 * +'
    >>> infix2postfix(u'(1+2)*3')
    u'1 2 + 3 *'

    # unary operators
    >>> infix2postfix(u'( -1+2) * -3-4')
    u'1 neg 2 + 3 neg * 4 -'

    >>> infix2postfix(u'1/2 == 3')
    u'1 2 / 3 =='
    >>> infix2postfix(u'1 < 2 or 3 < 4')
    u'1 2 < 3 4 < or'
    >>> infix2postfix(u'1 <= 2 and 3 >= 4')
    u'1 2 <= 3 4 >= and'
    >>> infix2postfix(u'7 & 3 != 0')
    u'7 3 & 0 !='

    >>> infix2postfix('not 4 + 1')
    u'4 1 + not'
    >>> infix2postfix('~A + 1')
    u'A ~ 1 +'

    """
    operator_stack = []
    output_string = []
    s = scanner(expression)
    while True:
        token_type, token = s.scan()
        #~ print token_type, token
        if token_type is None: break
        elif token_type == 'LEFT':
            operator_stack.append(token)
        elif token_type == 'VARIABLE':
            output_string.append(u'%s%s' % (variable_prefix, token))
        elif token_type == 'NUMBER':
            output_string.append(token)
        elif token_type == 'OPERATOR' or token_type == 'UNARYOPERATOR':
            if (not operator_stack
                    or operator_stack[-1] == '('
                    or precedence[operator_stack[-1]] < precedence[token]):
                operator_stack.append(token)
            else:
                while True:
                    output_string.append(operator_stack.pop())
                    if (not operator_stack
                            or operator_stack[-1] == '('
                            or precedence[token] >= precedence[operator_stack[-1]]):
                        break
                operator_stack.append(token)
        elif token_type == 'RIGHT':
            while operator_stack[-1] != '(':
                output_string.append(operator_stack.pop())
            operator_stack.pop()    # the '(' itself
        else:
            raise ValueError(u'unknown token: %r' % (token_type,))

    if '(' in operator_stack:
        raise ValueError('Unbalanced (, )')
    while operator_stack:
        output_string.append(operator_stack.pop())

    return u' '.join(unicode(s) for s in output_string)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

