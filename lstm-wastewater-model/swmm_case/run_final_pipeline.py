from __future__ import annotations

import json
from pathlib import Path

import build_final_leadership_report
import build_posterior_paper_artifacts
import run_midscale_validation


RESULT_DIR = Path(r"E:\PY\LSTM\swmm_case\paper_route_full_dim_results\midscale_ppd")


def print_key_metrics() -> None:
    summary = json.loads((RESULT_DIR / "full_dim_summary.json").read_text(encoding="utf-8"))
    print("\n=== 关键节点与指标 ===")
    print("真实异常点:", ", ".join(summary["truth_nodes"]))
    print("识别结果:", ", ".join(summary["predicted_nodes"]))
    print(f"Mean NSE: {summary['final_mean_nse']:.4f}")
    print(f"ACC: {summary['acc']:.4f}")
    print(f"MCC: {summary['mcc']:.4f}")
    print(f"AM 平均接受率: {summary['am_accept_rate_mean']:.4f}")
    print("结果目录:", RESULT_DIR)


def main() -> None:
    print("1/3 运行中参数验证...")
    run_midscale_validation.main()

    print("2/3 生成 posterior PPD 与收敛诊断...")
    import sys

    sys.argv = ["build_posterior_paper_artifacts.py", str(RESULT_DIR)]
    build_posterior_paper_artifacts.main()

    print("3/3 生成领导汇报材料与真值对比图...")
    build_final_leadership_report.main()

    print_key_metrics()
    print("\n完成。重点查看以下文件：")
    print(" - 项目最终汇报.md")
    print(" - 领导汇报总览.html")
    print(" - truth_vs_prediction_map.html")
    print(" - paper_posterior_ppd.html")
    print(" - paper_convergence_diagnostics.html")


if __name__ == "__main__":
    main()
