from pathlib import Path
import shutil
from pyswmm import Output
from swmm.toolkit.shared_enum import NodeAttribute

workdir = Path(r"E:\PY\LSTM\模型文件有污水量")
files = [
    workdir / "model_with_rain.out",
    workdir / "model_no_rain.out",
    workdir / "model_no_rain_pycopy.out",
    workdir / "盱眙污水管3（入渗点有雨水量）.out",
    workdir / "盱眙污水管3（入渗点无雨水量）.out",
]

src = workdir / "盱眙污水管3（入渗点无雨水量）.out"
dst = workdir / "model_no_rain_pycopy.out"
try:
    shutil.copyfile(src, dst)
    print("COPY_OK", dst, dst.exists(), dst.stat().st_size)
except Exception as e:
    print("COPY_ERR", repr(e))

for f in files:
    try:
        with Output(str(f)) as out:
            nodes = list(out.nodes)
            series = out.node_series(nodes[0], NodeAttribute.TOTAL_INFLOW)
            print("OPEN_OK", f.name, len(nodes), len(series), list(series.items())[:2])
    except Exception as e:
        print("OPEN_ERR", f.name, repr(e))
