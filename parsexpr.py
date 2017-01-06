import math

def analyze_str(s):
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
        if (l != 2 and ty == l) or (l == 2 and ts[-1] == x and '+*='.find(x) != -1):
            ts += x
        else:
            if l >= 0:
                r.append((l, ts))
            l = ty
            ts = x
    if l >= 0:
        r.append((l, ts))
    return r

def preprocess(analyzed):
    res = []
    op = 0
    opbase = 1024 # constant
    varidx = 2
    variables = ["e", "pi"]
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
            elif x[1] == "print":
                def temp_func(x):
                    global prints # better solutions?
                    prints += str(x) + " "
                r.append((1, (temp_func, op+3)))
            elif x[1] == "range":
                r.append((5, (0, op+2)))
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
                r.append((2, (lambda x,y:x/y, op+7)))
            elif x[1] == "(":
                op += opbase
            elif x[1] == ")":
                op -= opbase
            elif x[1] == "=":
                r.append((4, (0, op+4)))
            elif x[1] == ";":
                res.append(r)
                r = []
            elif x[1] == "==":
                r.append((2, (lambda x,y:1 if x==y else 0, op)))
            else:
                raise NameError("연산자 %s는 정의되지 않았습니다." % x[1])
    if len(r) > 0:
        res.append(r)
    return (res, varidx)

def calculate(ppeds):
    vals = [0 for i in range(ppeds[1])]
    vals[0],vals[1] = math.e,math.pi
    global prints
    prints = ""
    def no_method(p):
        for x in p:
            if x[0] != 0 and x[0] != 3:
                return False
        return True
    for pped in ppeds[0]:
        while not no_method(pped):
            idx = -1
            l = -1000000000000 # -inf
            for x in enumerate(pped):
                if x[1][0] != 0 and x[1][0] != 3 and ((x[1][0] != 4 and x[1][1][1] > l) or (x[1][0] == 4 and x[1][1][1] >= l)):
                    l = x[1][1][1]
                    idx = x[0]
            if pped[idx][0] == 1:
                if pped[idx+1][0] == 0 or pped[idx+1][0] == 3:
                    val = pped[idx+1][1]
                    if pped[idx+1][0] == 3:
                        val = lambda x=val:vals[x]
                    pped = pped[:idx] + [(0, lambda f=pped[idx][1][0],x=val: f(x()))] + pped[idx+2:]
                elif pped[idx+1][0] == 1:
                    func_a = pped[idx][1][0]
                    func_b = pped[idx+1][1][0]
                    function = lambda a,func_a=func_a,func_b=func_b:func_a(func_b(a))
                    pped = pped[:idx] + [(1, (function, max(pped[idx][1][1], pped[idx+1][1][1])))] + pped[idx+2:]
                else:
                    raise SyntaxError("단항 연산자에 이어 곧바로 이항 연산자가 등장할 수 없습니다.")
            elif pped[idx][0] == 2:
                val_a,val_b = pped[idx-1][1],pped[idx+1][1]
                if pped[idx-1][0] == 3:
                    val_a = lambda x=val_a:vals[x]
                if pped[idx+1][0] == 3:
                    val_b = lambda x=val_b:vals[x]
                pped = pped[:idx-1] + [(0, lambda func=pped[idx][1][0],x=val_a,y=val_b:func(x(), y()))] + pped[idx+2:]
            elif pped[idx][0] == 4:
                if pped[idx-1][0] == 3:
                    if pped[idx+1][0] == 0:
                        val = pped[idx+1][1]
                    elif pped[idx+1][0] == 3:
                        val = lambda x=pped[idx+1][1]:vals[x]
                    else:
                        raise SyntaxError("대입 연산자의 사용이 잘못되었습니다.")
                    subidx = pped[idx-1][1]
                    def func(s=subidx, v=val):
                        vals[s] = v()
                        return vals[s]
                    pped = pped[:idx-1] + [(0, func)] + pped[idx+2:]
                else:
                    raise SyntaxError("대입 연산자의 사용이 잘못되었습니다.")
            elif pped[idx][0] == 5:
                if (pped[idx-2][0] == 0 or pped[idx-2][0] == 3) and pped[idx-1][0] == 3 and (pped[idx+1][0] == 0 or pped[idx+1][0] == 3):
                    rangeto = pped[idx+1][1]
                    if pped[idx+1][1] == 3:
                        rangeto = lambda x=rangeto:vals[x]
                    execfunc = pped[idx-2][1]
                    if pped[idx-2][0] == 3:
                        execfunc = lambda x=execfunc:vals[x]
                    def temp_func2(f, v, i):
                        for j in range(i()):
                            vals[v] = j
                            f()
                    pped = pped[:idx-2] + [(0, lambda func=execfunc,var=pped[idx-1][1],rto=rangeto:temp_func2(func, var, rto))] + pped[idx+2:]
                else:
                    raise SyntaxError("range 구문의 사용이 잘못되었습니다.")
        if len(pped) > 0:
            a = pped[-1]
            if a[0] == 0:
                val = a[1]()
            else:
                val = vals[a[1]]
            
    if not (val is None):
        prints += str(val) + " "
    prints = prints.strip()
    if len(prints) > 0:
        return prints
    return "프로그램이 정상적으로 종료되었습니다."

def evaluate(s):
    return calculate(preprocess(analyze_str(s)))

if __name__ == "__main__":
    print(evaluate("(s = s + x * x) x range 5; print s"))
