from typing import List


head_string = 'MODULE main\n\
  VAR\n\
    c1: 0..4;\n\
    c2: 0..4;\n\
    c3: 0..4;\n\
    c4: 0..4;\n\
  INIT\n\
    c1 = 0 & c2 = 0 & c3 = 0 & c4 = 0\n'

class TransString:

    def __init__(self):
        self.string = ''
    
    def append(self, string):
        self.string += string
    
    def get(self):
        self.string = self.string[:-2]
        self.string = "TRANS\n"+self.string
        return self.string

class CTLSPECString:

    def __init__(self) -> None:
        self.cond = set()
    
    def append(self, string):
        self.cond.add(string)
    
    def get(self):
        all_cond = ''
        for cond in self.cond:
            all_cond += '\t({0}) |\n'.format(cond)
        all_cond = all_cond[:-2]
        string = 'CTLSPEC !EF!(\n{0}\n)'.format(all_cond)
        return string

def get_P(others: List):
    P_str = 'next(c{0})=c{0} & '
    P = ''
    for other in others:
        P += P_str.format(other)
    return P[:-2]

single_case_cond = 'c{0} = {1}'
single = '(case '+single_case_cond+': next(c{0}) = {2};\n\tTRUE: next(c{0}) = c{0};\nesac) & {P}|\n'
trans_case_cond = 'c{0} = {m} & c{1} = 0'
trans_case = 'case '+trans_case_cond+': next(c{0}) = 0 & next(c{1}) = {m};\n\tTRUE: next(c{0}) = c{0} & next(c{1}) = c{1};\nesac & {P}|\n'

trans = TransString()
spec = CTLSPECString()
M = [1, 2, 3]
C = [i for i in range(1, 5)]
for i in M:
    all = C.copy()
    all.remove(i)
    P = get_P(all)
    for c in C:
        if c != i:
            trans.append(single.format(i, 0, c, P=P))
            spec.append(single_case_cond.format(i, 0))
for i in C:
    all = C.copy()
    all.remove(i)
    P = get_P(all)
    trans.append(single.format(i, i%4+1, 0, P=P))
    spec.append(single_case_cond.format(i, i%4+1))
for i in C:
    n = i%4+1
    all = C.copy()
    all.remove(i)
    all.remove(i%4+1)
    P = get_P(all)
    for m in C:
        if m != n and m != i:
            trans.append(trans_case.format(i, i%4+1, m=m, n=n, P=P))
            spec.append(trans_case_cond.format(i, i%4+1, m=m, n=n))
trans_string = trans.get()
spec_string = spec.get()
with open('test.smv', 'w') as f:
    f.write(head_string)
    f.write(trans_string+'\n\n')
    f.write(spec_string)