# Config Reference

The full set of keys recognised by `doe.config.load_config`. Keys
beginning with `_` are ignored and reserved for inline documentation
(`scaffold-config` populates them with `_<key>_options` listing
alternatives).

## Top level

```json
{
  "metadata":      {...},
  "factors":       [...],
  "fixed_factors": {...},
  "responses":     [...],
  "constraints":   [...],
  "settings":      {...},
  "runner":        {...},
  "adaptive":      {...}
}
```

## `metadata`

Free-form. Used for the report header.

```json
"metadata": {
  "name":        "Reactor optimisation, July",
  "description": "Three reactor parameters, single yield response."
}
```

## `factors`

Ordered list. Each factor is either a long form (object) or a legacy
short form (`["name", "lo", "hi", ...]`).

```json
{
  "name":        "temperature",
  "type":        "continuous",        // continuous | ordinal | categorical
  "unit":        "C",
  "levels":      ["100", "200"],       // string-or-numeric strings
  "description": "Reactor jacket temp",
  "dtype":       "int",                // "" (auto) | "int" | "float"
  "role":        "subplot"             // subplot (default) | whole_plot (split-plot only)
}
```

`dtype: "int"` rounds *recommended* setpoints (from `optimize_surface`,
the stationary-point decoder, `model_guided` / `bayesian`,
`steepest_ascent`) to the nearest integer and clamps to the level
range — your generated runs were already integer-stringy if you typed
them as such; this affects what the optimiser hands back.

## `fixed_factors`

Flat dict; each entry is held constant across every run and passed to
`test_script` alongside the varied factors. Names that overlap with
`factors` are flagged at load time so you can't accidentally pass a
varied factor twice.

```json
"fixed_factors": {
  "buffer_volume_ml": "100",
  "stir_rate_rpm":    "200"
}
```

## `responses`

```json
{
  "name":        "yield",
  "optimize":    "maximize",   // maximize | minimize
  "unit":        "%",
  "weight":      1.0,           // for multi-objective desirability
  "bounds":      [0, 100],      // optional [low, high]
  "description": "Mol % converted"
}
```

## `constraints`

List of Python-syntax expression strings; runs that fail any constraint
are filtered out at design-generation time.

```json
"constraints": [
  "temperature + pressure <= 250",
  "catalyst != 'A' or temperature <= 150"
]
```

Allowed: arithmetic, comparisons, boolean logic, membership tests.
Banned: attribute access, function calls, imports.

## `settings`

| Key                   | Type   | Default            | Notes |
|-----------------------|--------|--------------------|-------|
| `operation`           | string | `full_factorial`   | One of: `full_factorial`, `plackett_burman`, `latin_hypercube`, `central_composite`, `fractional_factorial`, `box_behnken`, `definitive_screening`, `taguchi`, `d_optimal`, `mixture_simplex_lattice`, `mixture_simplex_centroid`, `linear_sweep`, `log_sweep`, `split_plot`. |
| `block_count`         | int    | `1`                | Replicate the design across this many blocks. |
| `replicate_center`    | int    | `0`                | Append N centre-point runs per block (numeric factors only). |
| `min_resolution`      | int    | `0` (auto)         | Fractional factorial: bump run count until at least this resolution. |
| `whole_plot_replicates` | int  | `1`                | Split-plot: replicates of each whole-plot (HTC) level. |
| `lhs_samples`         | int    | `0` (auto)         | Latin hypercube: explicit sample count. |
| `sweep_points`        | int    | `0` (auto)         | Linear/log sweep: explicit point count. |
| `test_script`         | string | `""`               | Path to the script the runner calls. |
| `out_directory`       | string | `"results"`        | Where `run_*.json` go. |
| `processed_directory` | string | `out_directory`    | Where plots / CSVs go. |

## `runner`

| Key            | Type   | Default       | Notes |
|----------------|--------|---------------|-------|
| `arg_style`    | string | `double-dash` | `double-dash` (`--name value`), `env` (`NAME=value`), `positional`. |
| `result_file`  | string | `json`        | Reserved for future result formats. |

## `adaptive`

Optional. Required for `doe next-batch` to do anything useful.

```json
"adaptive": {
  "strategy":                 "bayesian",  // refine | explore | balanced | model_guided | bayesian | multi_objective
  "batch_size":               4,
  "response_name":            "yield",     // focus a single response (refine/explore only)
  "stopping_effect_threshold": 0.0,
  "stopping_power_threshold":  0.0,
  "stopping_max_phases":      10
}
```
