from __future__ import annotations

import multiprocessing

from 运行0327_AM调优实验 import run_one_experiment


EXPERIMENT_NAME = "AM-R1"
EXPERIMENT_PARAMS = {
    "am_chain_count": 3,
    "am_samples_per_chain": 500,
    "am_warmup": 200,
    "am_adapt_start": 200,
    "am_initial_covariance": 0.001,
}


def main() -> None:
    run_one_experiment(EXPERIMENT_NAME, EXPERIMENT_PARAMS)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
