# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Targeted line-coverage tests for config, serve, simulate, mixture,
constraints, and runner modules.

These exercise the validation/error/defensive branches that the broader
functional test-suite doesn't reach, driving each assigned module to
100% line coverage. Everything is hermetic: tmp_path only, no fixed
ports (an ephemeral test server on 127.0.0.1 with guaranteed shutdown),
and deterministic inputs.
"""

from __future__ import annotations

import http.client
import http.server
import io
import json
import os
import socketserver
import sys
import threading
from functools import partial

import numpy as np
import pytest

from doe import config as config_mod
from doe.config import (
    _is_sweep_factor,
    _parse_factors,
    _parse_responses,
    _validate_config,
)
from doe.constraints import (
    ConstraintError,
    evaluate_constraint,
    filter_runs,
    parse_constraint,
)
from doe.mixture import fit_scheffe
from doe.models import (
    DesignMatrix,
    DOEConfig,
    ExperimentRun,
    Factor,
    ResponseVar,
    RunnerConfig,
)
from doe.runner import parse_factors
from doe.serve import _DoeHandler, serve
from doe.simulate import _resolve_target, _update_latest_symlink, simulate


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _cfg(factors, operation, responses=None, test_script="", fixed_factors=None):
    return DOEConfig(
        factors=factors,
        fixed_factors=fixed_factors or {},
        responses=responses or [ResponseVar(name="y")],
        block_count=1,
        test_script=test_script,
        operation=operation,
        processed_directory="",
        out_directory="results",
        runner=RunnerConfig(),
    )


def _matrix(runs, factor_names, operation="full_factorial"):
    return DesignMatrix(runs=runs, factor_names=factor_names, operation=operation)


# ===========================================================================
# config.py
# ===========================================================================

class TestConfigParsing:
    def test_legacy_factor_list_too_short(self):
        # line 90
        with pytest.raises(ValueError, match="at least one level"):
            _parse_factors([["only_name"]])

    def test_factor_unexpected_format(self):
        # line 93
        with pytest.raises(ValueError, match="Unexpected factor format"):
            _parse_factors([42])

    def test_response_dict_missing_name(self):
        # line 120
        with pytest.raises(ValueError, match="Response must have a name"):
            _parse_responses([{"optimize": "maximize"}])

    def test_is_sweep_factor_categorical(self):
        # line 168
        f = Factor(name="c", levels=["a", "b"], type="categorical")
        assert _is_sweep_factor(f) is False


class TestConfigValidation:
    def test_split_plot_no_subplot_factors(self):
        # line 206
        cfg = _cfg(
            [Factor(name="wp", levels=["a", "b"], role="whole_plot")],
            "split_plot",
        )
        with pytest.raises(ValueError, match="at least one subplot factor"):
            _validate_config(cfg)

    def test_dsd_too_few_factors(self):
        # lines 272, 273
        cfg = _cfg(
            [
                Factor(name="a", levels=["0", "1"], type="continuous"),
                Factor(name="b", levels=["0", "1"], type="continuous"),
            ],
            "definitive_screening",
        )
        with pytest.raises(ValueError, match="at least 3 factors"):
            _validate_config(cfg)

    def test_dsd_wrong_level_count(self):
        # lines 277, 278, 279
        cfg = _cfg(
            [
                Factor(name="a", levels=["0", "1"], type="continuous"),
                Factor(name="b", levels=["0", "1"], type="continuous"),
                Factor(name="c", levels=["0", "1", "2"], type="continuous"),
            ],
            "definitive_screening",
        )
        with pytest.raises(ValueError, match="exactly 2 levels"):
            _validate_config(cfg)

    def test_dsd_valid_numeric(self):
        # lines 277, 283, 284, 285 (passes cleanly)
        cfg = _cfg(
            [
                Factor(name="a", levels=["0", "10"], type="continuous"),
                Factor(name="b", levels=["0", "10"], type="continuous"),
                Factor(name="c", levels=["0", "10"], type="continuous"),
            ],
            "definitive_screening",
        )
        _validate_config(cfg)  # no error

    def test_dsd_non_numeric_levels(self):
        # lines 286, 287
        cfg = _cfg(
            [
                Factor(name="a", levels=["0", "10"], type="continuous"),
                Factor(name="b", levels=["0", "10"], type="continuous"),
                Factor(name="c", levels=["lo", "hi"], type="continuous"),
            ],
            "definitive_screening",
        )
        with pytest.raises(ValueError, match="non-numeric levels"):
            _validate_config(cfg)

    def test_linear_sweep_mixed_factors(self):
        # lines 293, 294, 295, 296, 297, 298 (numeric sweep + categorical passthrough)
        cfg = _cfg(
            [
                Factor(name="x", levels=["0", "10"], type="continuous"),
                Factor(name="c", levels=["a", "b"], type="categorical"),
            ],
            "linear_sweep",
        )
        _validate_config(cfg)  # no error

    def test_linear_sweep_non_numeric_defensive(self, monkeypatch):
        # lines 299, 300 -- defensive branch guarded by _is_sweep_factor;
        # simulate a future where the guard admits a non-numeric factor.
        monkeypatch.setattr(config_mod, "_is_sweep_factor", lambda f: True)
        cfg = _cfg(
            [Factor(name="x", levels=["abc", "def"], type="continuous")],
            "linear_sweep",
        )
        with pytest.raises(ValueError, match="requires numeric levels for 2-level"):
            _validate_config(cfg)

    def test_log_sweep_non_numeric_defensive(self, monkeypatch):
        # line 320 -- non-positive message check falls through to the
        # numeric-error raise when float() itself fails.
        monkeypatch.setattr(config_mod, "_is_sweep_factor", lambda f: True)
        cfg = _cfg(
            [Factor(name="x", levels=["abc", "def"], type="continuous")],
            "log_sweep",
        )
        with pytest.raises(ValueError, match="numeric positive levels"):
            _validate_config(cfg)

    def test_missing_test_script_warns(self, capsys):
        # line 345
        cfg = _cfg(
            [Factor(name="a", levels=["1", "2"])],
            "full_factorial",
            test_script="/no/such/script/at/all.sh",
        )
        _validate_config(cfg, strict=True)
        out = capsys.readouterr().out
        assert "does not exist" in out


# ===========================================================================
# serve.py
# ===========================================================================

class TestServeCov:
    def test_serve_keyboard_interrupt(self, tmp_path, monkeypatch, capsys):
        # lines 34, 35 -- serve_forever interrupted returns cleanly.
        def boom(self):
            raise KeyboardInterrupt

        monkeypatch.setattr(socketserver.TCPServer, "serve_forever", boom)
        serve(str(tmp_path), host="127.0.0.1", port=0)
        out = capsys.readouterr().out
        assert "Stopped." in out

    def test_list_directory_samefile_raises(self, tmp_path, monkeypatch):
        # lines 45-50 -- os.path.samefile raising falls through to super().
        handler = _DoeHandler.__new__(_DoeHandler)
        handler.directory = str(tmp_path)

        def raiser(a, b):
            raise OSError("cannot stat")

        sentinel = io.BytesIO(b"super-listing")
        monkeypatch.setattr(os.path, "samefile", raiser)
        monkeypatch.setattr(
            http.server.SimpleHTTPRequestHandler,
            "list_directory",
            lambda self, p: sentinel,
        )
        result = handler.list_directory(str(tmp_path))
        assert result is sentinel

    def test_root_index_and_subdir_over_http(self, tmp_path):
        # lines 52-76 (custom root index) and line 50 (subdir -> super).
        with_report = tmp_path / "session_a"
        with_report.mkdir()
        (with_report / "report.html").write_text("<html>rep</html>")
        no_report = tmp_path / "session_b"
        no_report.mkdir()
        (no_report / "run_1.json").write_text('{"y": 1}')
        # A plain file at root should be skipped (not a dir).
        (tmp_path / "readme.txt").write_text("hi")

        handler_factory = partial(_DoeHandler, directory=str(tmp_path))
        httpd = socketserver.TCPServer(("127.0.0.1", 0), handler_factory)
        httpd.timeout = 5
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            # Root -> custom DOE Sessions index.
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/")
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "DOE Sessions" in body
            assert "session_a" in body
            assert "report.html" in body
            assert "session_b" in body
            assert "no report" in body
            conn.close()

            # Subdirectory -> falls through to the default listing.
            conn2 = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn2.request("GET", "/session_b/")
            resp2 = conn2.getresponse()
            body2 = resp2.read().decode("utf-8")
            assert resp2.status == 200
            assert "run_1.json" in body2
            conn2.close()
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)


# ===========================================================================
# simulate.py
# ===========================================================================

class TestSimulateCov:
    def _matrix2(self):
        runs = [
            ExperimentRun(run_id=1, block_id=1, factor_values={"x": "1"}),
            ExperimentRun(run_id=2, block_id=1, factor_values={"x": "2"}),
        ]
        return _matrix(runs, ["x"])

    def test_func_raises_is_recorded(self, tmp_path, capsys):
        # lines 96-99
        cfg = _cfg([Factor(name="x", levels=["1", "2"])], "full_factorial")

        def boom(factors):
            raise RuntimeError("kaboom")

        out = simulate(self._matrix2(), cfg, func=boom, output_dir=str(tmp_path))
        err = capsys.readouterr().err
        assert "kaboom" in err
        assert not list(os.scandir(out)) or not any(
            f.name.startswith("run_") for f in os.scandir(out)
        )

    def test_non_dict_return(self, tmp_path):
        # lines 100, 101
        cfg = _cfg([Factor(name="x", levels=["1", "2"])], "full_factorial")
        with pytest.raises(ValueError, match="expected dict"):
            simulate(self._matrix2(), cfg, func=lambda f: 5, output_dir=str(tmp_path))

    def test_non_numeric_response(self, tmp_path):
        # lines 110, 111
        cfg = _cfg([Factor(name="x", levels=["1", "2"])], "full_factorial")
        with pytest.raises(ValueError, match="is not numeric"):
            simulate(
                self._matrix2(),
                cfg,
                func=lambda f: {"y": "not-a-number"},
                output_dir=str(tmp_path),
            )

    def test_session_copies_design_matrix(self, tmp_path):
        # line 82 -- design_matrix.json copied into the session dir.
        cfg = _cfg([Factor(name="x", levels=["1", "2"])], "full_factorial")
        base = tmp_path / "results"
        base.mkdir()
        (base / "design_matrix.json").write_text('{"runs": []}')
        out = simulate(
            self._matrix2(),
            cfg,
            func=lambda f: {"y": 1.0},
            output_dir=str(base),
            session_prefix="run",
        )
        assert os.path.isfile(os.path.join(out, "design_matrix.json"))


class TestResolveTargetCov:
    def test_file_not_found(self):
        # line 145
        with pytest.raises(FileNotFoundError, match="Simulator file not found"):
            _resolve_target("/no/such/file.py:sim")

    def test_unloadable_spec(self, tmp_path):
        # line 150 -- a path with no import loader (.txt suffix).
        p = tmp_path / "sim.txt"
        p.write_text("def sim(f):\n    return {}\n")
        with pytest.raises(ImportError, match="Could not load simulator"):
            _resolve_target(f"{p}:sim")

    def test_plain_module_import(self):
        # line 154
        func = _resolve_target("math:sqrt")
        assert func(4.0) == 2.0

    def test_missing_attribute(self):
        # line 157
        with pytest.raises(AttributeError, match="no 'definitely_absent'"):
            _resolve_target("math:definitely_absent")

    def test_non_callable_target(self):
        # line 162
        with pytest.raises(TypeError, match="is not callable"):
            _resolve_target("math:pi")


class TestUpdateLatestSymlinkCov:
    def test_replaces_existing_symlink(self, tmp_path):
        # lines 169, 170, 177
        base = tmp_path / "base"
        base.mkdir()
        (base / "old").mkdir()
        latest = base / "latest"
        latest.symlink_to("old")
        _update_latest_symlink(str(base), "new")
        assert os.readlink(latest) == "new"

    def test_refuses_non_symlink(self, tmp_path, capsys):
        # lines 171, 172, 176
        base = tmp_path / "base"
        base.mkdir()
        (base / "latest").write_text("i am a real file")
        _update_latest_symlink(str(base), "new")
        err = capsys.readouterr().err
        assert "not a symlink" in err
        assert (base / "latest").read_text() == "i am a real file"

    def test_symlink_oserror(self, tmp_path, monkeypatch, capsys):
        # lines 178, 179
        base = tmp_path / "base"
        base.mkdir()

        def raiser(src, dst):
            raise OSError("no symlinks here")

        monkeypatch.setattr(os, "symlink", raiser)
        _update_latest_symlink(str(base), "new")
        err = capsys.readouterr().err
        assert "could not update" in err


# ===========================================================================
# mixture.py
# ===========================================================================

class TestMixtureCov:
    def test_no_valid_runs(self):
        # line 80
        runs = [ExperimentRun(run_id=1, block_id=1, factor_values={"a": "1", "b": "0"})]
        assert fit_scheffe(runs, {}, ["a", "b"]) is None

    def test_too_few_components(self):
        # line 83
        runs = [ExperimentRun(run_id=1, block_id=1, factor_values={"a": "1"})]
        assert fit_scheffe(runs, {1: 5.0}, ["a"]) is None

    def test_bad_factor_values(self):
        # lines 91, 92 -- missing component key -> KeyError -> None
        runs = [ExperimentRun(run_id=1, block_id=1, factor_values={"a": "1"})]
        assert fit_scheffe(runs, {1: 5.0}, ["a", "b"]) is None

    def test_lstsq_linalg_error(self, monkeypatch):
        # lines 104, 105
        def raiser(*a, **k):
            raise np.linalg.LinAlgError("boom")

        monkeypatch.setattr(np.linalg, "lstsq", raiser)
        runs = [
            ExperimentRun(run_id=1, block_id=1, factor_values={"a": "1", "b": "0"}),
            ExperimentRun(run_id=2, block_id=1, factor_values={"a": "0", "b": "1"}),
        ]
        assert fit_scheffe(runs, {1: 10.0, 2: 20.0}, ["a", "b"]) is None

    def test_saturated_fit(self):
        # line 109 -- n <= p
        runs = [
            ExperimentRun(run_id=1, block_id=1,
                          factor_values={"a": "1", "b": "0", "c": "0"}),
            ExperimentRun(run_id=2, block_id=1,
                          factor_values={"a": "0", "b": "1", "c": "0"}),
            ExperimentRun(run_id=3, block_id=1,
                          factor_values={"a": "0", "b": "0", "c": "1"}),
        ]
        model = fit_scheffe(
            runs, {1: 10.0, 2: 20.0, 3: 30.0}, ["a", "b", "c"],
            model_form="quadratic",
        )
        assert model is not None
        assert np.isnan(model.r_squared)
        assert model.notes

    def _good_runs(self):
        runs = [
            ExperimentRun(run_id=1, block_id=1, factor_values={"a": "1", "b": "0"}),
            ExperimentRun(run_id=2, block_id=1, factor_values={"a": "0", "b": "1"}),
            ExperimentRun(run_id=3, block_id=1,
                          factor_values={"a": "0.5", "b": "0.5"}),
        ]
        return runs, {1: 10.0, 2: 20.0, 3: 14.0}

    def test_pinv_linalg_error(self, monkeypatch):
        # lines 136, 137 -- standard errors become NaN
        def raiser(*a, **k):
            raise np.linalg.LinAlgError("no pinv")

        monkeypatch.setattr(np.linalg, "pinv", raiser)
        runs, resp = self._good_runs()
        model = fit_scheffe(runs, resp, ["a", "b"], model_form="linear")
        assert model is not None
        assert all(t.std_error is None for t in model.terms)

    def test_scipy_missing(self, monkeypatch):
        # lines 141, 142 -- scipy.stats import fails -> no p-values
        monkeypatch.setitem(sys.modules, "scipy.stats", None)
        runs, resp = self._good_runs()
        model = fit_scheffe(runs, resp, ["a", "b"], model_form="linear")
        assert model is not None
        assert all(t.p_value is None for t in model.terms)


# ===========================================================================
# constraints.py
# ===========================================================================

class TestConstraintsCov:
    def test_syntax_error(self):
        # lines 46, 47
        with pytest.raises(ConstraintError, match="Invalid constraint syntax"):
            parse_constraint("x +")

    def test_evaluate_generic_error(self):
        # lines 86, 87 -- non-NameError failure during eval
        tree = parse_constraint("1 / 0")
        with pytest.raises(ConstraintError, match="failed to evaluate"):
            evaluate_constraint(tree, {"x": "1"}, "1 / 0")

    def test_filter_runs_no_constraints(self):
        # line 103
        runs = [ExperimentRun(run_id=1, block_id=1, factor_values={"x": "1"})]
        kept, dropped = filter_runs(runs, [])
        assert kept == runs
        assert dropped == []


# ===========================================================================
# runner.py
# ===========================================================================

class TestRunnerCov:
    def test_positional_missing_out(self):
        # line 86
        with pytest.raises(SystemExit, match="missing --out"):
            parse_factors(["x"], arg_style="positional", argv=["val"])

    def test_positional_missing_path(self):
        # line 90
        with pytest.raises(SystemExit, match="missing PATH"):
            parse_factors(["x"], arg_style="positional", argv=["val", "--out"])
