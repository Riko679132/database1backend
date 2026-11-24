# 27-Point VLE Checklist — Shen & Li 1992

- DOI: `10.1021/je00005a025`
- Expected: 27 40 °C low-pressure points (Table II 6, Table III 7, Table IV 7, Table V 7)
- Before Phase 3 (LLM batch): 6/27 matched; 6 extra high-pressure MDEA points
- After Phase 3 (deterministic parser): 27/27 matched; tables {'III': 7, 'II': 6, 'IV': 7, 'V': 7}
- Parser counts: {'tables': 4, 'all_points': 181, 'selected_40C_lowP': 27}

The original 12/27 figure was inflated by six evaluator false matches: the LLM extracted six >180 kPa MDEA points and the evaluator matched them to Table V MEA points because amine identity was only a penalty. After requiring amine identity, the true before coverage is 6/27.

| # | sample | amine | wt_a | wt_b | T (K) | P_CO2 (kPa) | loading | before | after | pipeline trace |
|---:|---:|---|---:|---:|---:|---:|---:|---|---|---|
| 1 | 31 | MDEA | 30.0 | None | 313.15 | 1.2 | 0.244 | matched_L3 | matched_L2 | PDF读=yes; 表格=II/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=matched_L3 |
| 2 | 32 | MDEA | 30.0 | None | 313.15 | 2.8 | 0.306 | matched_L3 | matched_L2 | PDF读=yes; 表格=II/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=matched_L3 |
| 3 | 33 | MDEA | 30.0 | None | 313.15 | 6.5 | 0.401 | matched_L3 | matched_L2 | PDF读=yes; 表格=II/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=matched_L3 |
| 4 | 34 | MDEA | 30.0 | None | 313.15 | 28.0 | 0.672 | matched_L3 | matched_L2 | PDF读=yes; 表格=II/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=matched_L3 |
| 5 | 35 | MDEA | 30.0 | None | 313.15 | 72.8 | 0.811 | matched_L3 | matched_L2 | PDF读=yes; 表格=II/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=matched_L3 |
| 6 | 36 | MDEA | 30.0 | None | 313.15 | 140.3 | 0.911 | matched_L3 | matched_L2 | PDF读=yes; 表格=II/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=matched_L3 |
| 7 | 37 | MEA | 12.0 | 18.0 | 313.15 | 1.0 | 0.357 | missing | matched_L2 | PDF读=yes; 表格=III/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 8 | 38 | MEA | 12.0 | 18.0 | 313.15 | 3.7 | 0.441 | missing | matched_L2 | PDF读=yes; 表格=III/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 9 | 39 | MEA | 12.0 | 18.0 | 313.15 | 9.0 | 0.488 | missing | matched_L2 | PDF读=yes; 表格=III/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 10 | 40 | MEA | 12.0 | 18.0 | 313.15 | 17.4 | 0.536 | missing | matched_L2 | PDF读=yes; 表格=III/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 11 | 41 | MEA | 12.0 | 18.0 | 313.15 | 45.9 | 0.608 | missing | matched_L2 | PDF读=yes; 表格=III/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 12 | 42 | MEA | 12.0 | 18.0 | 313.15 | 107.4 | 0.684 | missing | matched_L2 | PDF读=yes; 表格=III/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 13 | 43 | MEA | 12.0 | 18.0 | 313.15 | 157.5 | 0.71 | missing | matched_L2 | PDF读=yes; 表格=III/组1/p.3; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 14 | 44 | MEA | 24.0 | 6.0 | 313.15 | 2.9 | 0.473 | missing | matched_L2 | PDF读=yes; 表格=IV/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 15 | 45 | MEA | 24.0 | 6.0 | 313.15 | 6.6 | 0.5 | missing | matched_L2 | PDF读=yes; 表格=IV/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 16 | 46 | MEA | 24.0 | 6.0 | 313.15 | 11.6 | 0.51 | missing | matched_L2 | PDF读=yes; 表格=IV/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 17 | 47 | MEA | 24.0 | 6.0 | 313.15 | 29.4 | 0.549 | missing | matched_L2 | PDF读=yes; 表格=IV/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 18 | 48 | MEA | 24.0 | 6.0 | 313.15 | 52.4 | 0.584 | missing | matched_L2 | PDF读=yes; 表格=IV/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 19 | 49 | MEA | 24.0 | 6.0 | 313.15 | 82.2 | 0.612 | missing | matched_L2 | PDF读=yes; 表格=IV/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 20 | 50 | MEA | 24.0 | 6.0 | 313.15 | 132.2 | 0.637 | missing | matched_L2 | PDF读=yes; 表格=IV/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 21 | 51 | MEA | 30.0 | None | 313.15 | 2.2 | 0.471 | missing | matched_L2 | PDF读=yes; 表格=V/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 22 | 52 | MEA | 30.0 | None | 313.15 | 5.0 | 0.496 | missing | matched_L2 | PDF读=yes; 表格=V/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 23 | 53 | MEA | 30.0 | None | 313.15 | 12.8 | 0.512 | missing | matched_L2 | PDF读=yes; 表格=V/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 24 | 54 | MEA | 30.0 | None | 313.15 | 28.7 | 0.538 | missing | matched_L2 | PDF读=yes; 表格=V/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 25 | 55 | MEA | 30.0 | None | 313.15 | 58.4 | 0.57 | missing | matched_L2 | PDF读=yes; 表格=V/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 26 | 56 | MEA | 30.0 | None | 313.15 | 101.3 | 0.594 | missing | matched_L2 | PDF读=yes; 表格=V/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |
| 27 | 57 | MEA | 30.0 | None | 313.15 | 140.1 | 0.62 | missing | matched_L2 | PDF读=yes; 表格=V/组1/p.4; LLM=deterministic_parser(not_llm); 结构化=yes; 校验=L2; before=missing |

## Missing and extra

- Missing after fix: 0
- Extra before fix (>180 kPa or other non-reference points): 6
- The extra MDEA points are valid VLE observations but were outside the reference's 40 °C, ≤180 kPa selection; they remain L3 in the Phase-3 batch and are not counted as matched.
