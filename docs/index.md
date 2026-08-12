# DOE Helper

A Python CLI tool that automates the creation and analysis of experimental
designs. It generates reproducible design matrices, creates executable runner
scripts, and analyzes results using classical DOE techniques including ANOVA,
response surface modeling, and multi-objective optimization.

The project includes **221 worked use cases** spanning HPC, cloud
infrastructure, networking, food science, agriculture, manufacturing, sports,
and many more domains — each with a full configuration, simulated results, and
analysis walkthrough. Browse them in
[`doe/use_cases/`](https://github.com/MartinGallagher-code/design_of_experiments/tree/main/doe/use_cases).

## Installation

The package is published on PyPI at
[pypi.org/project/doehelper](https://pypi.org/project/doehelper/) — install the
latest release with:

```bash
pip install doehelper
```

Or clone the repository for development:

```bash
git clone https://github.com/MartinGallagher-code/design_of_experiments.git
cd design_of_experiments
pip install -e ".[dev]"
```

The CLI installs as `doe`. Run `doe --help` to list every subcommand.

## Where to start

- **[User Guide](user_guide.md)** — a practical tour of the tool, from first
  config to a finished analysis report.
- **[DOE Fundamentals](doe_fundamentals.md)** — a primer on Design of
  Experiments concepts and how they map onto the tool.
- **[Cookbook](cookbook.md)** — recipes for common tasks.
- **[Adaptive Strategies](strategies.md)** — when to pick which adaptive
  strategy.

## Reference

- **[Command Reference](commands.md)** — every CLI subcommand and its options.
- **[Config Reference](config.md)** — the experiment configuration format.
- **[Public API](api.md)** — the stable Python API and its compatibility
  guarantees.

## Links

- Project website: [doehelper.com](https://doehelper.com)
- Source code: [github.com/MartinGallagher-code/design_of_experiments](https://github.com/MartinGallagher-code/design_of_experiments)
- Issue tracker: [GitHub Issues](https://github.com/MartinGallagher-code/design_of_experiments/issues)
- Changelog: [CHANGELOG.md](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/CHANGELOG.md)

## License

DOE Helper is licensed under the
[GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0).
