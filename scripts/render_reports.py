#!/usr/bin/env python3
"""
Pre-render markdown reports for the KG browser.

Generates .md report files and plot thumbnails from the tvbo database YAML files.
Supports: models (dynamics), coupling functions, integrators, observation models.

Output:
    odoo-addons/tvbo/static/src/reports/{category}/Name.md
    odoo-addons/tvbo/static/src/img/thumbnails/coupling_functions/Name.png

Usage:
    python scripts/render_reports.py
    python scripts/render_reports.py --force
    python scripts/render_reports.py --name JansenRit
    python scripts/render_reports.py --category coupling_functions
"""

import argparse
import glob
import os
import re
import sys

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLATFORM_ROOT = os.path.dirname(SCRIPT_DIR)
ADDON_DIR = os.path.join(PLATFORM_ROOT, "odoo-addons", "tvbo")
REPORTS_DIR = os.path.join(ADDON_DIR, "static", "src", "reports")

# Resolve tvbo database location
DEFAULT_DB = None
_candidates = ["/tmp/tvbo/database"]
for _c in _candidates:
    if os.path.isdir(_c):
        DEFAULT_DB = _c
        break

if DEFAULT_DB is None:
    try:
        import tvbo
        DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(tvbo.__file__)), "database")
    except ImportError:
        DEFAULT_DB = os.path.join(os.path.expanduser("~"), "tools", "tvbo", "database")


def _canon(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def render_model_reports(db_root: str, force: bool = False, name_filter: str | None = None):
    """Generate markdown reports for all models using Dynamics.generate_report()."""
    from tvbo import Dynamics

    model_dir = os.path.join(db_root, "models")
    out_dir = os.path.join(REPORTS_DIR, "models")
    _ensure_dir(out_dir)

    yaml_files = []
    for ext in ("*.yaml", "*.yml"):
        yaml_files.extend(glob.glob(os.path.join(model_dir, "**", ext), recursive=True))

    ok, fail = 0, 0
    for path in sorted(yaml_files):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            continue
        model_name = raw.get("name", os.path.splitext(os.path.basename(path))[0])

        if name_filter and _canon(name_filter) != _canon(model_name):
            continue

        out_path = os.path.join(out_dir, f"{model_name}.md")
        if not force and os.path.isfile(out_path):
            print(f"  [skip] {model_name}.md (exists)")
            ok += 1
            continue

        try:
            model = Dynamics.from_file(path)
            report_md = model.generate_report()
            if report_md:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(str(report_md))
                print(f"  [ok]   {model_name}.md")
                ok += 1
            else:
                print(f"  [FAIL] {model_name}: empty report")
                fail += 1
        except Exception as e:
            print(f"  [FAIL] {model_name}: {e}")
            fail += 1

    print(f"  Models: {ok} ok, {fail} failed")


def render_coupling_reports(db_root: str, force: bool = False, name_filter: str | None = None):
    """Generate markdown reports and plot thumbnails for all coupling functions."""
    from sympy import symbols, sympify, latex, lambdify
    import numpy as np

    cf_dir = os.path.join(db_root, "coupling_functions")
    out_dir = os.path.join(REPORTS_DIR, "coupling_functions")
    thumb_dir = os.path.join(ADDON_DIR, "static", "src", "img", "thumbnails", "coupling_functions")
    _ensure_dir(out_dir)
    _ensure_dir(thumb_dir)

    yaml_files = []
    for ext in ("*.yaml", "*.yml"):
        yaml_files.extend(glob.glob(os.path.join(cf_dir, "**", ext), recursive=True))

    ok, fail = 0, 0
    for path in sorted(yaml_files):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            continue
        cf_name = raw.get("name", os.path.splitext(os.path.basename(path))[0])

        if name_filter and _canon(name_filter) != _canon(cf_name):
            continue

        out_path = os.path.join(out_dir, f"{cf_name}.md")
        thumb_path = os.path.join(thumb_dir, f"{cf_name}.png")

        if not force and os.path.isfile(out_path) and os.path.isfile(thumb_path):
            print(f"  [skip] {cf_name} (exists)")
            ok += 1
            continue

        try:
            md = _coupling_report_md(raw)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md)

            _coupling_plot(raw, thumb_path)
            print(f"  [ok]   {cf_name}")
            ok += 1
        except Exception as e:
            print(f"  [FAIL] {cf_name}: {e}")
            fail += 1

    print(f"  Coupling functions: {ok} ok, {fail} failed")


def _coupling_report_md(raw: dict) -> str:
    """Generate markdown report for a coupling function from its YAML dict.

    Uses tvbo.Coupling.symbolic() for the full summation equation.
    """
    from sympy import latex, Symbol
    from tvbo import Coupling

    name = raw.get("name", "Unknown")
    pre_rhs = raw.get("pre_expression", {}).get("rhs", "")
    post_rhs = raw.get("post_expression", {}).get("rhs", "")
    params = raw.get("parameters", {})
    delayed = raw.get("delayed", False)
    sparse = raw.get("sparse", False)

    md = [f"## {name}", ""]

    # Full symbolic equation via Coupling class
    try:
        c = Coupling(name=name, use_ontology=True)
        sym_eq = c.symbolic()
        sym_latex = latex(sym_eq)
        md.append("### Coupling Equation")
        md.append("")
        md.append(f"$$c_i = {sym_latex}$$")
        md.append("")
    except Exception:
        # Fallback: show pre/post separately
        if pre_rhs or post_rhs:
            md.append("### Coupling Equation")
            md.append("")
            if pre_rhs:
                md.append(f"**Pre-synaptic:** `{pre_rhs}`")
                md.append("")
            if post_rhs:
                md.append(f"**Post-synaptic:** `{post_rhs}`")
                md.append("")

    # Properties
    md.append("### Properties")
    md.append("")
    md.append(f"- **Delayed:** {'Yes' if delayed else 'No'}")
    md.append(f"- **Sparse:** {'Yes' if sparse else 'No'}")
    md.append("")

    # Parameters table
    if params:
        md.append("### Parameters")
        md.append("")
        md.append("| Name | Default | Description |")
        md.append("|------|---------|-------------|")
        for pname, pdata in params.items():
            val = pdata.get("value", "") if isinstance(pdata, dict) else pdata
            desc = pdata.get("description", "") if isinstance(pdata, dict) else ""
            md.append(f"| ${latex(Symbol(pname))}$ | {val} | {desc} |")
        md.append("")

    return "\n".join(md)


def _coupling_plot(raw: dict, out_path: str):
    """Generate a clean coupling function thumbnail (no axes/grids/titles).

    Shows coupling behavior at different amplitudes using viridis colormap.
    For trivial pre-expressions (x_j), plots post(w * x_j).
    For non-trivial pre-expressions, plots w * pre(x_j).
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    import numpy as np
    from sympy import sympify, lambdify, Symbol

    name = raw.get("name", "")
    pre_rhs = raw.get("pre_expression", {}).get("rhs", "")
    post_rhs = raw.get("post_expression", {}).get("rhs", "")
    params = raw.get("parameters", {})

    # Build parameter substitutions
    param_subs = {}
    for pname, pdata in params.items():
        val = pdata.get("value", 1.0) if isinstance(pdata, dict) else pdata
        try:
            param_subs[Symbol(pname)] = float(val)
        except (ValueError, TypeError):
            param_subs[Symbol(pname)] = 1.0

    x_i, x_j = Symbol('x_i'), Symbol('x_j')
    gx = Symbol('gx')

    # Parse pre-expression
    local_pre = {'x_i': x_i, 'x_j': x_j, **{p: Symbol(p) for p in params}}
    try:
        pre_expr = sympify(pre_rhs, locals=local_pre)
    except Exception:
        pre_expr = x_j

    pre_is_trivial = (pre_expr == x_j)

    # Determine x-range based on parameters and coupling type
    if "Kuramoto" in name:
        lo, hi = -np.pi, np.pi
    elif pre_is_trivial and post_rhs:
        # For post-expression couplings, scale range based on sigma/midpoint
        sigma = param_subs.get(Symbol('sigma'), 1.0)
        midpoint = param_subs.get(Symbol('midpoint'), 0.0)
        a_val = param_subs.get(Symbol('a'), 1.0)
        # Range covers the full sigmoid transition
        spread = max(abs(4 * sigma / a_val), 10)
        lo, hi = midpoint - spread, midpoint + spread
    else:
        lo, hi = -10, 10

    x_vals = np.linspace(lo, hi, 300)

    # Amplitude values (coupling weight w)
    amplitudes = np.linspace(0.2, 2.0, 10)
    cmap = plt.cm.viridis
    norm = Normalize(vmin=amplitudes.min(), vmax=amplitudes.max())

    fig, ax = plt.subplots(figsize=(3, 3))

    if pre_is_trivial and post_rhs:
        local_post = {'gx': gx, **{p: Symbol(p) for p in params}}
        try:
            post_expr = sympify(post_rhs, locals=local_post)
        except Exception:
            post_expr = gx
        post_num = post_expr.subs(param_subs)

        free = post_num.free_symbols
        if gx in free:
            fn = lambdify(gx, post_num, "numpy")
            for w in amplitudes:
                y = fn(w * x_vals)
                ax.plot(x_vals, y, color=cmap(norm(w)), linewidth=2, alpha=0.85)
        else:
            for w in amplitudes:
                y = float(post_num) * w * x_vals
                ax.plot(x_vals, y, color=cmap(norm(w)), linewidth=2, alpha=0.85)
    else:
        pre_num = pre_expr.subs(param_subs)
        if x_i in pre_num.free_symbols:
            pre_num = pre_num.subs(x_i, 0)

        free = pre_num.free_symbols
        if len(free) >= 1:
            var = x_j if x_j in free else list(free)[0]
            fn = lambdify(var, pre_num, "numpy")
            for w in amplitudes:
                y = w * fn(x_vals)
                ax.plot(x_vals, y, color=cmap(norm(w)), linewidth=2, alpha=0.85)
        else:
            val = float(pre_num)
            for w in amplitudes:
                ax.axhline(w * val, color=cmap(norm(w)), linewidth=2, alpha=0.85)

    # Clean thumbnail: no axes, no grid, no title
    ax.set_axis_off()
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out_path, dpi=150, bbox_inches='tight', pad_inches=0.05, facecolor='white')
    plt.close(fig)


def render_integrator_reports(db_root: str, force: bool = False, name_filter: str | None = None):
    """Generate markdown reports for all integrators."""
    from sympy import Symbol, latex, sympify

    int_dir = os.path.join(db_root, "integrators")
    out_dir = os.path.join(REPORTS_DIR, "integrators")
    _ensure_dir(out_dir)

    yaml_files = []
    for ext in ("*.yaml", "*.yml"):
        yaml_files.extend(glob.glob(os.path.join(int_dir, "**", ext), recursive=True))

    ok, fail = 0, 0
    for path in sorted(yaml_files):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            continue
        int_name = raw.get("method", os.path.splitext(os.path.basename(path))[0])

        if name_filter and _canon(name_filter) != _canon(int_name):
            continue

        out_path = os.path.join(out_dir, f"{int_name}.md")
        if not force and os.path.isfile(out_path):
            print(f"  [skip] {int_name}.md (exists)")
            ok += 1
            continue

        try:
            md = _integrator_report_md(raw)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"  [ok]   {int_name}.md")
            ok += 1
        except Exception as e:
            print(f"  [FAIL] {int_name}: {e}")
            fail += 1

    print(f"  Integrators: {ok} ok, {fail} failed")


def _integrator_report_md(raw: dict) -> str:
    """Generate markdown report for an integrator from its YAML dict."""
    from sympy import Symbol, latex, sympify

    method = raw.get("method", "Unknown")
    step_size = raw.get("step_size", "")
    duration = raw.get("duration", "")
    n_stages = raw.get("number_of_stages", "")
    delayed = raw.get("delayed", False)

    md = [f"## {method}", ""]

    # Properties
    md.append("### Properties")
    md.append("")
    md.append(f"- **Step size:** {step_size}")
    md.append(f"- **Duration:** {duration}")
    if n_stages:
        md.append(f"- **Number of stages:** {n_stages}")
    md.append(f"- **Delayed:** {'Yes' if delayed else 'No'}")
    md.append("")

    # Intermediate expressions
    intermediates = raw.get("intermediate_expressions", {})
    if intermediates:
        md.append("### Intermediate Expressions")
        md.append("")
        for iname, idata in intermediates.items():
            eq = idata.get("equation", {})
            rhs = eq.get("rhs", "")
            lhs = eq.get("lhs", iname)
            md.append(f"**{lhs}:**")
            md.append(f"```")
            md.append(rhs)
            md.append(f"```")
            md.append("")

    # Update expression
    update = raw.get("update_expression", {})
    if update:
        eq = update.get("equation", {})
        rhs = eq.get("rhs", "")
        lhs = eq.get("lhs", "")
        md.append("### Update Rule")
        md.append("")
        md.append(f"**{lhs}:**")
        md.append(f"```")
        md.append(rhs)
        md.append(f"```")
        md.append("")

    return "\n".join(md)


def render_observation_model_reports(db_root: str, force: bool = False, name_filter: str | None = None):
    """Generate markdown reports for all observation models."""
    obs_dir = os.path.join(db_root, "observation_models")
    out_dir = os.path.join(REPORTS_DIR, "observation_models")
    _ensure_dir(out_dir)

    yaml_files = []
    for ext in ("*.yaml", "*.yml"):
        yaml_files.extend(glob.glob(os.path.join(obs_dir, "**", ext), recursive=True))

    ok, fail = 0, 0
    for path in sorted(yaml_files):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            continue
        obs_name = raw.get("name", os.path.splitext(os.path.basename(path))[0])

        if name_filter and _canon(name_filter) != _canon(obs_name):
            continue

        out_path = os.path.join(out_dir, f"{obs_name}.md")
        if not force and os.path.isfile(out_path):
            print(f"  [skip] {obs_name}.md (exists)")
            ok += 1
            continue

        try:
            md = _observation_model_report_md(raw)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"  [ok]   {obs_name}.md")
            ok += 1
        except Exception as e:
            print(f"  [FAIL] {obs_name}: {e}")
            fail += 1

    print(f"  Observation models: {ok} ok, {fail} failed")


def _observation_model_report_md(raw: dict) -> str:
    """Generate markdown report for an observation model from its YAML dict."""
    name = raw.get("name", "Unknown")
    desc = raw.get("description", "")
    modality = raw.get("imaging_modality", "")
    period = raw.get("period", "")
    params = raw.get("parameters", {})
    pipeline = raw.get("pipeline", [])

    md = [f"## {name}", ""]

    if desc:
        md.append(desc)
        md.append("")

    # Properties
    props = []
    if modality:
        props.append(f"- **Imaging modality:** {modality}")
    if period:
        props.append(f"- **Period:** {period} ms")
    if props:
        md.append("### Properties")
        md.append("")
        md.extend(props)
        md.append("")

    # Parameters
    if params:
        md.append("### Parameters")
        md.append("")
        md.append("| Name | Default | Unit | Description |")
        md.append("|------|---------|------|-------------|")
        for pname, pdata in params.items():
            if isinstance(pdata, dict):
                val = pdata.get("value", "")
                unit = pdata.get("unit", "")
                pdesc = pdata.get("description", "")
            else:
                val, unit, pdesc = pdata, "", ""
            md.append(f"| {pname} | {val} | {unit} | {pdesc} |")
        md.append("")

    # Pipeline
    if pipeline:
        md.append("### Processing Pipeline")
        md.append("")
        for i, step in enumerate(pipeline, 1):
            step_name = step.get("name", f"Step {i}")
            output = step.get("output", "")
            eq = step.get("equation", {})
            rhs = eq.get("rhs", "")
            md.append(f"**{i}. {step_name}**")
            if output:
                md.append(f"  Output: `{output}`")
            if rhs:
                md.append(f"  ```")
                md.append(f"  {rhs}")
                md.append(f"  ```")
            # Step parameters
            step_params = eq.get("parameters", {})
            args = step.get("arguments", [])
            if step_params:
                for sp_name, sp_data in step_params.items():
                    if isinstance(sp_data, dict):
                        md.append(f"  - {sp_name} = {sp_data.get('value', '')} ({sp_data.get('description', '')})")
            if args:
                for arg in args:
                    if isinstance(arg, dict):
                        md.append(f"  - {arg.get('name', '')} = {arg.get('value', '')} ({arg.get('description', '')})")
            md.append("")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Pre-render reports for the KG browser")
    parser.add_argument("--database", default=DEFAULT_DB,
                        help=f"Path to tvbo database/ directory (default: {DEFAULT_DB})")
    parser.add_argument("--force", action="store_true",
                        help="Re-render even if report already exists")
    parser.add_argument("--name", help="Render only a specific item (by name)")
    parser.add_argument("--category", choices=["models", "coupling_functions", "integrators", "observation_models"],
                        help="Render only a specific category")
    args = parser.parse_args()

    db_root = os.path.abspath(args.database)
    if not os.path.isdir(db_root):
        print(f"Error: database directory not found: {db_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Database: {db_root}")
    print(f"Output:   {REPORTS_DIR}")
    print()

    categories = {
        "models": ("Rendering model reports...", render_model_reports),
        "coupling_functions": ("Rendering coupling function reports...", render_coupling_reports),
        "integrators": ("Rendering integrator reports...", render_integrator_reports),
        "observation_models": ("Rendering observation model reports...", render_observation_model_reports),
    }

    for key, (msg, fn) in categories.items():
        if args.category and args.category != key:
            continue
        print(msg)
        fn(db_root, force=args.force, name_filter=args.name)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
