# kipalang
# Copyright (C) 2016-2017  kipa00
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import math
import signal

buffer_size = 0
timeout_second = 0

class BufferOverflowError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class TimeExpiredError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

def analyze_str(s):
    string = False
    def character_set(c):
        if c == ' ':
            return -1
        if "0123456789.".find(c) != -1:
            return 0
        if "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_".find(c) != -1:
            return 1
        return 2
    l = -1
    r = []
    ts = ""
    for x in s:
        ty = character_set(x)
        if x == '"':
            if l >= 0:
                r.append((l, ts))
            string = not string
            if string:
                ts = ""
                l = 3
            else:
                l = -1
        elif not string:
            if (l != 2 and ty == l) or (l == 2 and ts[-1] == x and '+*='.find(x) != -1):
                ts += x
            else:
                if l >= 0:
                    r.append((l, ts))
                l = ty
                ts = x
        else:
            ts += x
    if l >= 0:
        r.append((l, ts))
    return r

def preprocess(analyzed):
    op = 0
    opbase = 1024 # constant
    variables = ["e", "pi", "list"]
    varidx = len(variables)
    r = []
    for x in analyzed:
        if x[0] == 0:
            if x[1].find(".") == -1:
                r.append((0, lambda a=int(x[1]):a))
            else:
                r.append((0, lambda a=float(x[1]):a))
        elif x[0] == 1:
            if x[1] == "sin":
                r.append((1, (math.sin, op+10)))
            elif x[1] == "cos":
                r.append((1, (math.cos, op+10)))
            elif x[1] == "tan":
                r.append((1, (math.tan, op+10)))
            elif x[1] == "exp":
                r.append((1, (math.exp, op+10)))
            elif x[1] == "log":
                r.append((1, (math.log, op+10)))
            elif x[1] == "pow":
                r.append((2, (math.pow, op+8)))
            elif x[1] == "print":
                def temp_func(x):
                    global prints # better solutions?
                    before_len = len(prints)
                    def to_string(l):
                        if isinstance(l, list):
                            return "(" + ", ".join(map(to_string, l)) + ")"
                        return str(l)
                    prints += to_string(x) + " "
                    if buffer_size > 0 and len(prints) > buffer_size:
                        raise BufferOverflowError(prints[:buffer_size])
                    return len(prints) - before_len - 1
                r.append((1, (temp_func, op+10)))
            elif x[1] == "putch":
                def putch_func(x):
                    global prints # better solutions?
                    if isinstance(x, list):
                        prints += "".join(map(chr, x))
                        x = x[-1] if len(x) > 0 else None
                    else:
                        prints += chr(x)
                    if buffer_size > 0 and len(prints) > buffer_size:
                        raise BufferOverflowError(prints[:buffer_size])
                    return x
                r.append((1, (putch_func, op+10)))
            elif x[1] == "in":
                r.append((5, (0, op+2)))
            elif x[1] == "range":
                r.append((1, (lambda x:list(range(x))if not isinstance(x,list)else(list(range(x[0],x[0]+x[1]))if len(x)==2 else list(range(x[0],x[0]+x[1]*x[2],x[2]))), op+10)))
            elif x[1] == "while":
                r.append((8, (0, op+2)))
            elif x[1] == "len":
                r.append((1, (lambda x:len(x) if isinstance(x, list) else 1, op+10)))
            else:
                try:
                    idx = variables.index(x[1])
                except ValueError:
                    idx = varidx
                    varidx += 1
                    variables.append(x[1])
                r.append((3, idx))
        elif x[0] == 2:
            if x[1] == "+":
                if len(r) > 0 and (r[-1][0] == 0 or r[-1][0] == 3):
                    r.append((2, (lambda x,y:x+y, op+6)))
                else:
                    r.append((1, (lambda x:x, op+10)))
            elif x[1] == "-":
                if len(r) > 0 and (r[-1][0] == 0 or r[-1][0] == 3):
                    r.append((2, (lambda x,y:x-y, op+6)))
                else:
                    r.append((1, (lambda x:-x, op+10)))
            elif x[1] == "*" or x[1] == "×":
                r.append((2, (lambda x,y:x*y, op+7)))
            elif x[1] == "/":
                r.append((2, (lambda x,y:x//y if isinstance(x, int) and isinstance(x, int) else x/y, op+7)))
            elif x[1] == "(":
                op += opbase
            elif x[1] == ")":
                op -= opbase
            elif x[1] == "[":
                if len(r) > 0:
                    if r[-1][0] == 3:
                        r.append((7, (0, op+11)))
                    else:
                        def temp_func3(x, y):
                            if not isinstance(x, list):
                                x = [x]
                            try:
                                return x[y]
                            except IndexError as e:
                                raise IndexError("목록의 색인이 범위 밖을 참조했습니다. (크기: %d, 참조됨: %d)" % (len(x), y))
                            except TypeError as e:
                                raise IndexError("목록의 색인 형이 잘못되었습니다.")
                        r.append((2, (temp_func3, op+11)))
                else:
                    raise IndexError("배열 앞에서만 참조가 가능합니다.")
                op += opbase
            elif x[1] == "]":
                op -= opbase
            elif x[1] == "=":
                if len(r) > 0 and r[-1][0] == 2:
                    r[-1] = (4, (r[-1][1][0], op+4))
                else:
                    r.append((4, (lambda x,y:y, op+4)))
            elif x[1] == ";":
                r.append((2, (lambda x,y:y, op)))
            elif x[1] == "==":
                r.append((2, (lambda x,y:1 if x==y else 0, op+5)))
            elif x[1] == "<":
                r.append((2, (lambda x,y:1 if x<y else 0, op+5)))
            elif x[1] == ">":
                r.append((2, (lambda x,y:1 if x>y else 0, op+5)))
            elif x[1] == "%":
                r.append((2, (lambda x,y:x%y, op+7)))
            elif x[1] == ",":
                def temp_func2(x, y):
                    if not isinstance(x, list):
                        x = [x]
                    if not isinstance(y, list):
                        y = [y]
                    return x + y
                r.append((2, (temp_func2, op)))
            else:
                raise NameError("연산자 %s는 정의되지 않았습니다." % x[1])
        elif x[0] == 3:
            r.append((0, lambda x=list(map(ord, x[1])): x))
    return (r, varidx)

def calculate(ppeds):
    vals = [0 for i in range(ppeds[1])]
    vals[0],vals[1],vals[2] = math.e,math.pi,[]
    global prints
    prints = ""
    def no_method(p):
        for x in p:
            if x[0] != 0 and x[0] != 3:
                return False
        return True
    def to_value_func(p):
        if p[0] == 0:
            return p[1]
        elif p[0] == 3:
            return lambda x=p[1]: vals[x]
        elif p[0] == 6:
            return lambda x=p[1][0],y=p[1][1]: vals[x][y()] if isinstance(vals[x], list) else vals[x]
        raise TypeError("연산자는 평가될 수 없습니다.")
    is_value_type = lambda x:x[0]==0 or x[0]==3 or x[0]==6
    pped = ppeds[0]
    while not no_method(pped):
        idx = -1
        l = -1000000000000 # -inf
        for x in enumerate(pped):
            if not is_value_type(x[1]) and ((x[1][0] != 4 and x[1][1][1] > l) or (x[1][0] == 4 and x[1][1][1] >= l)):
                l = x[1][1][1]
                idx = x[0]
        if pped[idx][0] == 1:
            if is_value_type(pped[idx+1]):
                val = to_value_func(pped[idx+1])
                pped = pped[:idx] + [(0, lambda f=pped[idx][1][0],x=val: f(x()))] + pped[idx+2:]
            elif pped[idx+1][0] == 1:
                func_a = pped[idx][1][0]
                func_b = pped[idx+1][1][0]
                function = lambda a,func_a=func_a,func_b=func_b:func_a(func_b(a))
                pped = pped[:idx] + [(1, (function, max(pped[idx][1][1], pped[idx+1][1][1])))] + pped[idx+2:]
            else:
                raise SyntaxError("단항 연산자에 이어 곧바로 이항 연산자가 등장할 수 없습니다.")
        elif pped[idx][0] == 2:
            val_a,val_b = to_value_func(pped[idx-1]),to_value_func(pped[idx+1])
            pped = pped[:idx-1] + [(0, lambda func=pped[idx][1][0],x=val_a,y=val_b:func(x(), y()))] + pped[idx+2:]
        elif pped[idx][0] == 4:
            if pped[idx-1][0] == 3:
                val = to_value_func(pped[idx+1])
                subidx = pped[idx-1][1]
                def func(s=subidx, v=val, f=pped[idx][1][0]):
                    vals[s] = f(vals[s], v())
                    return vals[s]
                pped = pped[:idx-1] + [(0, func)] + pped[idx+2:]
            elif pped[idx-1][0] == 6:
                val = to_value_func(pped[idx+1])
                subidx = pped[idx-1][1]
                def func(s=subidx, v=val, f=pped[idx][1][0]):
                    idx = s[1]()
                    vals[s[0]][idx] = f(vals[s[0]][idx], v())
                    return vals[s[0]][idx]
                pped = pped[:idx-1] + [(0, func)] + pped[idx+2:]
            else:
                raise SyntaxError("대입 연산자의 사용이 잘못되었습니다.")
        elif pped[idx][0] == 5:
            if is_value_type(pped[idx-2]) and pped[idx-1][0] == 3 and is_value_type(pped[idx+1]):
                rangeto = to_value_func(pped[idx+1])
                execfunc = to_value_func(pped[idx-2])
                def temp_func2(f, v, i):
                    li = i()
                    res = []
                    if not isinstance(li, list):
                        li = [li]
                    for j in li:
                        vals[v] = j
                        res.append(f())
                    return res
                pped = pped[:idx-2] + [(0, lambda func=execfunc,var=pped[idx-1][1],rto=rangeto:temp_func2(func, var, rto))] + pped[idx+2:]
            else:
                raise SyntaxError("in 구문의 사용이 잘못되었습니다.")
        elif pped[idx][0] == 7:
            val = to_value_func(pped[idx+1])
            pped = pped[:idx-1] + [(6, (pped[idx-1][1], val))] + pped[idx+2:]
        elif pped[idx][0] == 8:
            def temp_func3(x, y):
                while y():
                    x()
            pped = pped[:idx-1] + [(0, lambda x=to_value_func(pped[idx-1]),y=to_value_func(pped[idx+1]):temp_func3(x,y))] + pped[idx+2:]
    if len(pped) > 0:
        a = pped[-1]
        if a[0] == 0:
            val = a[1]()
        else:
            val = vals[a[1]]
    prints = prints.strip()
    if len(prints) > 0:
        return prints
    return "프로그램이 정상적으로 종료되었습니다."

def evaluate(s):
    try:
        if timeout_second > 0:
            def timeout(signum, frame):
                raise TimeExpiredError(prints)
            signal.signal(signal.SIGALRM, timeout)
            signal.alarm(timeout_second)
        res = calculate(preprocess(analyze_str(s)))
        signal.alarm(0)
    except Exception as e:
        signal.alarm(0)
        raise e
    return res

def setBufferSize(l=0):
    global buffer_size
    buffer_size = l

def setTimeout(t=0):
    global timeout_second
    timeout_second = t

setBufferSize(444)

if __name__ == "__main__":
    while True:
        try:
            print(evaluate(input(">>> ")))
        except KeyboardInterrupt:
            break
        except:
            print("오류: %s" % sys.exc_info()[1])
