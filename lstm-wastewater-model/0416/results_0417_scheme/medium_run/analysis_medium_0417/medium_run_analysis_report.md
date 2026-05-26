# 0417 medium run analysis

Truth replay: mean_nse=1.000000, sse=1.081e-29
Recommended solution: posterior_best_map

Final solution comparison:
                solution  mean_nse      sse  truth_mass  outside_mass  l1_error  l2_error                                                       top5
      posterior_best_map  0.999696 0.000865    0.663760      0.336240  0.672479  0.428594 J11:0.3269; J20:0.3158; J84:0.2914; J72:0.0236; J48:0.0211
                 ga_best  0.996540 0.007796    0.631234      0.368766  0.737531  0.444048 J20:0.3180; J11:0.3133; J72:0.2865; J75:0.0428; J31:0.0388
posterior_median_summary  0.992032 0.025240    0.544629      0.455371  0.910742  0.359261 J11:0.3310; J20:0.1530; J21:0.0875; J84:0.0647; J48:0.0606

Stage stats JSON:
{
  "truth_check": {
    "mean_nse": 1.0,
    "sse": 1.0809126378111386e-29
  },
  "ga_all": {
    "rows": 1152,
    "best_mean_nse": 0.9965404097367032,
    "median_mean_nse": 0.7353796461648725,
    "min_mean_nse": -0.5156477058726113
  },
  "ga_last": {
    "rows": 96,
    "best_mean_nse": 0.9965404097367032,
    "median_mean_nse": 0.8212023832016917,
    "min_mean_nse": 0.3837963174740109,
    "unique_rounded_5": 93
  },
  "initial_ppd": {
    "rows": 63,
    "best_mean_nse": 0.9965404097367032,
    "median_mean_nse": 0.8757104023847035,
    "min_mean_nse": 0.609701680430769,
    "unique_rounded_5": 63
  },
  "am": {
    "rows": 4800,
    "chains": 8,
    "mean_accept_rate": 0.4058333333333333,
    "accept_rate_by_chain": {
      "0": 0.49166666666666664,
      "1": 0.4166666666666667,
      "2": 0.3283333333333333,
      "3": 0.38333333333333336,
      "4": 0.3933333333333333,
      "5": 0.43833333333333335,
      "6": 0.3416666666666667,
      "7": 0.4533333333333333
    },
    "best_log_like": -0.6818486574863118,
    "best_log_like_mean_nse": 0.99969603872385,
    "best_mean_nse": 0.9997415963185587,
    "median_mean_nse": 0.997890266349833,
    "ppd_rows": 3600,
    "ppd_best_mean_nse": 0.9997415963185587,
    "ppd_median_mean_nse": 0.997890917986539
  },
  "coverage": {
    "mean_coverage_90": 0.6690909090909091,
    "min_coverage_90": 0.3182608695652174,
    "max_coverage_90": 0.8469565217391304
  },
  "summary": {
    "run_mode": "0417 medium run",
    "solution_scores": {
      "ga_best": {
        "mean_nse": 0.9965404097367031,
        "sse": 0.007796225230108787
      },
      "posterior_best_map": {
        "mean_nse": 0.9996960387238499,
        "sse": 0.0008652250312130376
      },
      "posterior_median_summary": {
        "mean_nse": 0.9920319546781545,
        "sse": 0.025239800313776796
      }
    },
    "recommended_solution_name": "posterior_best_map",
    "final_solution_name": "posterior_best_map",
    "posterior_median_top3": [
      "J11",
      "J20",
      "J21"
    ],
    "ga_last_score_stats": {
      "max_mean_nse": 0.9965404097367031,
      "median_mean_nse": 0.8212023832016917,
      "min_mean_nse": 0.38379631747401094,
      "unique_count": 96
    },
    "initial_ppd_count": 63,
    "initial_ppd_score_stats": {
      "max_mean_nse": 0.9965404097367031,
      "median_mean_nse": 0.8757104023847035,
      "min_mean_nse": 0.609701680430769
    },
    "posterior_validation_sample_count": 64,
    "posterior_coverage_mean": 0.6690909090909091,
    "am_accept_rate_by_chain": {
      "0": 0.49166666666666664,
      "1": 0.4166666666666667,
      "2": 0.3283333333333333,
      "3": 0.38333333333333336,
      "4": 0.3933333333333333,
      "5": 0.43833333333333335,
      "6": 0.3416666666666667,
      "7": 0.4533333333333333
    },
    "config": {
      "ga_population_count": 4,
      "ga_population_size": 24,
      "ga_generations": 12,
      "ga_elite_ratio": 0.12,
      "ga_mutation_strength": 0.2,
      "ga_migration_interval": 4,
      "ga_migration_count": 1,
      "ga_competition_replace_count": 1,
      "ga_dedup_decimals": 5,
      "am_chain_count": 8,
      "am_samples_per_chain": 600,
      "am_warmup": 150,
      "am_adapt_start": 150,
      "am_initial_covariance": 0.0015,
      "am_eps": 1e-08,
      "initial_ppd_keep_fraction": 0.75,
      "initial_ppd_min_count": 48,
      "initial_ppd_min_mean_nse": -100.0,
      "initial_ppd_max_nse_drop": 0.5,
      "initial_ppd_rank_pressure": 1.5,
      "am_start_weighted": true,
      "am_use_prior_in_acceptance": false,
      "am_use_initial_ppd_covariance": true,
      "am_prior_kernel_scale": 0.01,
      "am_proposal_method": "tangent_projected_gaussian",
      "posterior_validation_samples": 64,
      "parallel_workers": 8,
      "random_seed": 20260416,
      "progress_step_interval": 25
    },
    "data_paths": {
      "output_dir": "E:\\PY\\LSTM\\0416\\results_0417_scheme\\medium_run"
    }
  }
}

Per-monitor NSE:
solution   ga_best  posterior_best_map  posterior_median_summary
monitor                                                         
J25       0.997157            0.999879                  0.992194
J27       0.993404            0.999880                  0.999531
J47       0.997240            0.999562                  0.974583
J49       0.997244            0.999566                  0.974540
J62       0.995173            0.999504                  0.999935
J61       0.995172            0.999504                  0.999935
J9        0.995173            0.999598                  0.998982
J50       0.995171            0.999597                  0.976996
J7        0.997008            0.999854                  0.996650
J75       0.999599            0.999855                  0.999384
J78       0.999604            0.999857                  0.999621

Figures:
- fig1_ga_convergence.png
- fig2_solution_shares.png
- fig3_posterior_weights.png
- fig4_am_traces.png
- fig5_per_monitor_nse.png
- fig6_coverage.png
- fig7_final_curves.png