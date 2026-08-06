# Project Roadmap

This document outlines the vision and planned direction for DOE Helper.

## Vision

DOE Helper is a production-ready, feature-rich tool for automating experimental design and analysis. We aim to make Design of Experiments accessible to researchers and engineers across all domains while maintaining scientific rigor and ease of use.

### Guiding Principles

1. **Accessibility**: Simplified CLI for common workflows, detailed docs for advanced use
2. **Reproducibility**: Deterministic designs with seed control, documented analysis methods
3. **Extensibility**: Clear APIs for custom designs and analyses
4. **Robustness**: Comprehensive error handling and edge case support
5. **Performance**: Efficient computation for large designs (100+ factors)

## Current Status

**Version**: 0.4.0 (Stable)

- 14 design types fully implemented
- Comprehensive ANOVA and response surface analysis
- Multi-objective optimization with adaptive strategies
- 221 worked use cases across multiple domains
- Full CLI with documentation
- mypy strict typing enforced in CI, ~90% test coverage
- Security scanning (pip-audit, bandit), REUSE compliance, SBOM on release

## Roadmap by Priority

### Phase 1: Production Hardening (v0.3.x)
**Target**: Q3 2026

- [x] Full type hints on public APIs (mypy strict)
- [x] 80%+ test coverage enforcement
- [x] Integration test suite
- [x] Dependency security scanning
- [x] SBOM generation for releases
- [x] Formal API stability documentation

**Status**: Completed in v0.4.0 (#40)

### Phase 2: Enhanced Analysis (v0.4.0)
**Target**: Q4 2026

- [ ] Generalized linear models (logistic regression, Poisson GLM)
- [ ] Bayesian analysis options (credible intervals, posterior visualization)
- [ ] Advanced diagnostics: studentized residuals, DFFITS
- [ ] Monte Carlo uncertainty quantification
- [ ] Interaction visualization and analysis enhancements

### Phase 3: Cloud & Scale (v0.5.0)
**Target**: Q1 2027

- [ ] AWS Lambda/EC2 runner integration
- [ ] Google Cloud integration (Cloud Run, Dataflow)
- [ ] Distributed parallel execution across machines
- [ ] Cloud storage backends (S3, GCS)
- [ ] Cost estimation and monitoring

### Phase 4: Interactive Tools (v0.6.0)
**Target**: H2 2027

- [ ] Optional web dashboard (view results, manage designs)
- [ ] Real-time experiment monitoring
- [ ] Interactive design exploration
- [ ] D3/Plotly visualizations
- [ ] Collaborative features (share designs, results)

## Known Limitations

1. **Categorical encoding**: Limited to one-hot; ordinal categorical improvements planned
2. **High-dimensional design**: 50+ factors may be slow in some designs
3. **Real-time execution**: No live progress updates during experiment runs
4. **GUI**: CLI-only (web UI planned for v0.6.0)

## Non-Goals

These features are explicitly out of scope (at least for the current roadmap):

- **Custom statistical distributions**: Use R/Python scipy for specialty distributions
- **Machine learning models**: Use scikit-learn, XGBoost for predictive modeling
- **Real-time 3D visualization**: Visualization is static/HTML
- **Commercial support tier**: Free/open-source only
- **Graphical experiment orchestration**: Focus is CLI + API

## Community Contributions Welcome

We encourage contributions in these areas:

- **New design types**: Screening designs, optimal designs for specific domains
- **Analysis enhancements**: Novel diagnostics, visualizations
- **Use case templates**: Real-world examples from your field
- **Documentation**: Tutorials, cookbook recipes, video guides
- **Performance**: Optimization for large designs, Numba compilation

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Release Frequency

- **Patch releases** (0.3.x): As bugs are found (roughly every 2-4 weeks)
- **Minor releases** (0.x.0): Quarterly or as features are ready
- **Major releases** (x.0.0): When breaking changes are necessary (rare)

## Versioning & API Stability

- **Python support**: 3.9+; dropping 3.9 requires major version bump
- **CLI interface**: Stable across minor versions; changes trigger major bump
- **Configuration format**: Backwards compatible; new keys have defaults
- **Public APIs**: Documented functions stable across minor versions

See [docs/api.md](docs/api.md) for detailed stability guarantees.

## Feedback

Your feedback shapes the roadmap:

- **Ideas**: Open an issue with the `enhancement` label
- **Bugs**: Report with the `bug` label and version info
- **Use cases**: Share your domain or workflow — helps prioritize features
- **Questions**: Use [Discussions](https://github.com/MartinGallagher-code/design_of_experiments/discussions)

## Maintainer Notes

See [docs/RELEASE.md](docs/RELEASE.md) for release procedures and [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

---

Last updated: July 20, 2026
