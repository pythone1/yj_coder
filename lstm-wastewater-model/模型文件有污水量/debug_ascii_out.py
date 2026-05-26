import os
from pyswmm import Output
from swmm.toolkit.shared_enum import NodeAttribute

os.chdir(r"C:\swmm_temp")
for f in ["model_with_rain.out", "model_no_rain.out"]:
    try:
        with Output(f) as out:
            nodes = list(out.nodes)
            series = out.node_series(nodes[0], NodeAttribute.TOTAL_INFLOW)
            print("OK", f, len(nodes), len(series), list(series.items())[:2])
    except Exception as e:
        print("ERR", f, repr(e))
