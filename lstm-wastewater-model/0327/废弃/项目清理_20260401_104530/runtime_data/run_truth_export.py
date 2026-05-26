# -*- coding: utf-8 -*-
from swmm.toolkit import solver
inp = r'E:\PY\LSTM\0327\export_ascii\truth_injection_package\truth_injection_model.inp'
rpt = r'E:\PY\LSTM\0327\export_ascii\truth_injection_package\truth_injection_model.rpt'
out = r'E:\PY\LSTM\0327\export_ascii\truth_injection_package\truth_injection_model.out'
solver.swmm_run(inp, rpt, out)
print('DONE')
print(inp)
print(rpt)
print(out)
