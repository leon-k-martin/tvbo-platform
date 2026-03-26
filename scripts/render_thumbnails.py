#!/usr/bin/env python3
"""
Render thumbnail images for the KG browser.

Generates PNG thumbnails for models (simulation traces), networks (connectivity
matrices), and atlases (parcellation surfaces) from the tvbo database YAML files.

Output goes to odoo-addons/tvbo/static/src/img/thumbnails/{models,networks,atlases}/
and is served by Odoo at /tvbo/static/src/img/thumbnails/...

Usage:
    # Render all thumbnails (skip existing)
    python scripts/render_thumbnails.py

    # Force re-render all
    python scripts/render_thumbnails.py --force

    # Render only models
    python scripts/render_thumbnails.py --only models

    # Render a specific model
    python scripts/render_thumbnails.py --only models --name JansenRit

    # Use custom tvbo database path
    python scripts/render_thumbnails.py --database /path/to/tvbo/database
"""

import argparse
import glob
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import bsplot.style
bsplot.style.use("tvbo")
import matplotlib.pyplot as plt
import yaml


# --------------------------------------------------------------------- paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLATFORM_ROOT = os.path.dirname(SCRIPT_DIR)
ADDON_DIR = os.path.join(PLATFORM_ROOT, "odoo-addons", "tvbo")
STATIC_IMG = os.path.join(ADDON_DIR, "static", "src", "img", "thumbnails")

# Default tvbo database location — try the docker-compose mount path,
# then resolve from the tvbo package install if available
DEFAULT_DB = None
_candidates = [
    "/tmp/tvbo/database",  # docker-compose mount
]
for _c in _candidates:
    if os.path.isdir(_c):
        DEFAULT_DB = _c
        break

if DEFAULT_DB is None:
    try:
        import tvbo
        DEFAULT_DB = str(tvbo.database_path)
    except (ImportError, AttributeError):
        DEFAULT_DB = os.path.join(os.path.expanduser("~"), "tools", "tvbo", "tvbo", "database")


# ------------------------------------------------------------------ helpers
def _canon(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _safe_filename(name: str) -> str:
    """Sanitize a name for use as a filename (no colons, slashes, etc.)."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


# --------------------------------------------------------- model thumbnails
def render_model_thumbnail(yaml_path: str, out_path: str) -> bool:
    """Run a short simulation and plot state variable traces."""
    from tvbo import Dynamics

    model = Dynamics.from_file(yaml_path)
    res = model.run(duration=100)
    fig, ax = plt.subplots(figsize=(2.0, 2.0), dpi=150)
    res.plot(ax=ax, legend=False)
    ax.set_axis_off()
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.savefig(out_path, bbox_inches="tight", transparent=True, pad_inches=0)
    plt.close(fig)
    return True


def render_models(db_root: str, force: bool = False, name_filter: str | None = None):
    """Render thumbnails for all models in database/models/."""
    model_dir = os.path.join(db_root, "models")
    out_dir = os.path.join(STATIC_IMG, "models")
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

        out_path = os.path.join(out_dir, f"{model_name}.png")
        if not force and os.path.isfile(out_path):
            print(f"  [skip] {model_name}.png (exists)")
            ok += 1
            continue

        try:
            render_model_thumbnail(path, out_path)
            print(f"  [ok]   {model_name}.png")
            ok += 1
        except Exception as e:
            print(f"  [FAIL] {model_name}: {e}")
            fail += 1

    print(f"  Models: {ok} ok, {fail} failed")


# ------------------------------------------------------- network thumbnails
def render_network_thumbnail(yaml_path: str, out_path: str) -> bool:
    """Plot the connectivity weight matrix as a heatmap."""
    from tvbo.data.network_io import load_network

    net = load_network(yaml_path)
    weights = net.weights_matrix
    if weights is None or weights.size == 0:
        return False

    fig, ax = plt.subplots(figsize=(2.0, 2.0), dpi=150)
    ax.imshow(weights, cmap="viridis", interpolation="none")
    ax.set_axis_off()
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.savefig(out_path, bbox_inches="tight", transparent=True, pad_inches=0)
    plt.close(fig)
    return True


def render_networks(db_root: str, force: bool = False, name_filter: str | None = None):
    """Render thumbnails for all networks in database/networks/."""
    net_dir = os.path.join(db_root, "networks")
    out_dir = os.path.join(STATIC_IMG, "networks")
    _ensure_dir(out_dir)

    yaml_files = []
    for ext in ("*.yaml", "*.yml"):
        yaml_files.extend(glob.glob(os.path.join(net_dir, "**", ext), recursive=True))

    ok, fail = 0, 0
    for path in sorted(yaml_files):
        stem = os.path.splitext(os.path.basename(path))[0]

        if name_filter and _canon(name_filter) != _canon(stem):
            continue

        out_path = os.path.join(out_dir, f"{stem}.png")
        if not force and os.path.isfile(out_path):
            print(f"  [skip] {stem}.png (exists)")
            ok += 1
            continue

        try:
            if render_network_thumbnail(path, out_path):
                print(f"  [ok]   {stem}.png")
                ok += 1
            else:
                print(f"  [FAIL] {stem}: empty weights matrix")
                fail += 1
        except Exception as e:
            print(f"  [FAIL] {stem}: {e}")
            fail += 1

    print(f"  Networks: {ok} ok, {fail} failed")


# --------------------------------------------------------- atlas thumbnails
def _resolve_atlas_annot(yaml_path: str, db_root: str) -> str:
    """Map an atlas YAML file name to a LH FreeSurfer annot file."""
    base = os.path.basename(yaml_path).lower()
    extra_dir = os.path.join(db_root, "_extra")
    candidates = [
        ("yeo17", "lh.Yeo2011_17Networks_N1000.annot"),
        ("yeo2011", "lh.Yeo2011_17Networks_N1000.annot"),
        ("desikan", "lh.aparc.annot"),
        ("desikan-killiany", "lh.aparc.annot"),
        ("desikankilliany", "lh.aparc.annot"),
        ("destrieux", "lh.aparc.a2009s.annot"),
        ("a2009", "lh.aparc.a2009s.annot"),
        ("hcpmmp1", "lh.HCP-MMP1.annot"),
    ]
    for key, fname in candidates:
        if key in base:
            p = os.path.join(extra_dir, fname)
            if os.path.isfile(p):
                return p
    return ""


def render_atlas_thumbnail(yaml_path: str, out_path: str, db_root: str) -> bool:
    """Render a parcellation on a brain surface."""
    import nibabel as nib
    from bsplot.surface import plot_surf
    from matplotlib.colors import ListedColormap

    annot_path = _resolve_atlas_annot(yaml_path, db_root)
    if not annot_path:
        return False

    labels, ctab, _names = nib.freesurfer.io.read_annot(annot_path)
    cmap = ListedColormap(ctab[:, :3] / 255.0)
    fig, ax = plt.subplots()
    plot_surf(
        surface="fsaverage",
        overlay=labels,
        surface_density="164k",
        hemi="lh",
        view="lateral",
        parcellated=True,
        cmap=cmap,
        surface_suffix="pial",
        ax=ax,
    )
    ax.set_axis_off()
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.savefig(out_path, bbox_inches="tight", transparent=True, pad_inches=0, dpi=300)
    plt.close(fig)
    return True


def render_atlases(db_root: str, force: bool = False, name_filter: str | None = None):
    """Render thumbnails for all atlases in database/atlases/."""
    atlas_dir = os.path.join(db_root, "atlases")
    out_dir = os.path.join(STATIC_IMG, "atlases")
    _ensure_dir(out_dir)

    yaml_files = []
    for ext in ("*.yaml", "*.yml"):
        yaml_files.extend(glob.glob(os.path.join(atlas_dir, "**", ext), recursive=True))

    ok, fail = 0, 0
    for path in sorted(yaml_files):
        stem = os.path.splitext(os.path.basename(path))[0]

        if name_filter and _canon(name_filter) != _canon(stem):
            continue

        out_path = os.path.join(out_dir, f"{stem}.png")
        if not force and os.path.isfile(out_path):
            print(f"  [skip] {stem}.png (exists)")
            ok += 1
            continue

        try:
            if render_atlas_thumbnail(path, out_path, db_root):
                print(f"  [ok]   {stem}.png")
                ok += 1
            else:
                print(f"  [FAIL] {stem}: no matching annot file")
                fail += 1
        except Exception as e:
            print(f"  [FAIL] {stem}: {e}")
            fail += 1

    print(f"  Atlases: {ok} ok, {fail} failed")


# ----------------------------------------------------- integrator thumbnails
def render_integrator_thumbnail(yaml_path: str, out_path: str) -> bool:
    """Plot integrator scheme visualization (Butcher tableau style)."""
    import numpy as np

    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        return False

    method = raw.get("method", "")
    n_stages = raw.get("number_of_stages", 1)
    step_size = raw.get("step_size", 1.0)

    # Simple visualization: solve dy/dt = -y with the integrator's number of stages
    # shown as colored dots on an exponential decay curve
    fig, ax = plt.subplots(figsize=(2.0, 2.0), dpi=150)
    t = np.linspace(0, 4, 200)
    y = np.exp(-t)
    ax.plot(t, y, color="#3498DB", linewidth=2, alpha=0.8)

    # Show stage evaluations as dots
    if n_stages and isinstance(n_stages, (int, float)) and n_stages > 0:
        stage_t = np.linspace(0, 4, int(n_stages) + 1)
        stage_y = np.exp(-stage_t)
        ax.scatter(stage_t, stage_y, color="#2C3E50", s=30, zorder=5)

    ax.set_axis_off()
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.savefig(out_path, bbox_inches="tight", transparent=True, pad_inches=0)
    plt.close(fig)
    return True


def render_integrators(db_root: str, force: bool = False, name_filter: str | None = None):
    """Render thumbnails for all integrators."""
    int_dir = os.path.join(db_root, "integrators")
    out_dir = os.path.join(STATIC_IMG, "integrators")
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
        name = raw.get("method", os.path.splitext(os.path.basename(path))[0])

        if name_filter and _canon(name_filter) != _canon(name):
            continue

        out_path = os.path.join(out_dir, f"{name}.png")
        if not force and os.path.isfile(out_path):
            print(f"  [skip] {name}.png (exists)")
            ok += 1
            continue

        try:
            if render_integrator_thumbnail(path, out_path):
                print(f"  [ok]   {name}.png")
                ok += 1
            else:
                print(f"  [FAIL] {name}: invalid YAML")
                fail += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            fail += 1

    print(f"  Integrators: {ok} ok, {fail} failed")


# --------------------------------------------------- experiment thumbnails
def render_experiment_thumbnail(yaml_path: str, out_path: str) -> bool:
    """Generate a summary card-style thumbnail for an experiment.

    Shows a schematic diagram of the experiment components:
    dynamics, observations, algorithms, optimizations, etc.
    """
    import numpy as np

    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        return False

    # Collect components
    components = []

    # Dynamics: check multiple locations
    dyn = raw.get("dynamics") or raw.get("model") or raw.get("network", {}).get("dynamics")
    if dyn:
        if isinstance(dyn, dict):
            names = []
            for k, v in dyn.items():
                if isinstance(v, dict) and v.get("name"):
                    names.append(v["name"])
            if names:
                components.append(("Dynamics", ", ".join(names[:2])))
            elif dyn.get("name"):
                components.append(("Dynamics", dyn["name"]))
            else:
                components.append(("Dynamics", ""))
        elif isinstance(dyn, str):
            components.append(("Dynamics", dyn))
        else:
            components.append(("Dynamics", str(dyn)))

    if raw.get("network"):
        components.append(("Network", ""))

    obs = raw.get("observations") or raw.get("observation_models")
    if obs:
        if isinstance(obs, dict):
            obs_names = [v.get("name", k) for k, v in obs.items() if isinstance(v, dict)]
        elif isinstance(obs, list):
            obs_names = [o.get("name", "") for o in obs if isinstance(o, dict)]
        else:
            obs_names = []
        components.append(("Observations", ", ".join(obs_names[:3])))

    for key, label in [("algorithms", "Algorithms"), ("explorations", "Explorations"),
                       ("optimizations", "Optimizations"), ("continuations", "Continuations")]:
        section = raw.get(key)
        if section:
            if isinstance(section, dict):
                names = list(section.keys())[:3]
            elif isinstance(section, list):
                names = [s.get("name", "") for s in section if isinstance(s, dict)][:3]
            else:
                names = []
            components.append((label, ", ".join(names)))

    if not components:
        return False

    # Draw a clean component diagram
    fig, ax = plt.subplots(figsize=(2.5, 2.0), dpi=150)
    n = len(components)
    colors = plt.cm.Set2(np.linspace(0, 0.8, max(n, 1)))

    for i, (comp_type, comp_detail) in enumerate(components):
        y = 1.0 - (i / max(n - 1, 1)) * 0.8 if n > 1 else 0.6
        rect = plt.Rectangle((0.05, y - 0.06), 0.9, 0.11,
                              facecolor=colors[i], edgecolor="#2C3E50",
                              linewidth=0.8, alpha=0.85, transform=ax.transAxes)
        ax.add_patch(rect)
        text = comp_type
        if comp_detail:
            text += f": {comp_detail[:20]}"
        ax.text(0.5, y, text, transform=ax.transAxes, ha="center", va="center",
                fontsize=5, fontweight="bold", color="#2C3E50")

    # Draw arrows between components
    for i in range(n - 1):
        y_top = 1.0 - (i / max(n - 1, 1)) * 0.8 if n > 1 else 0.6
        y_bot = 1.0 - ((i + 1) / max(n - 1, 1)) * 0.8 if n > 1 else 0.6
        ax.annotate("", xy=(0.5, y_bot + 0.06), xytext=(0.5, y_top - 0.06),
                     xycoords="axes fraction", textcoords="axes fraction",
                     arrowprops=dict(arrowstyle="->", color="#718096", lw=0.8))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.savefig(out_path, bbox_inches="tight", transparent=True, pad_inches=0)
    plt.close(fig)
    return True


def render_experiments(db_root: str, force: bool = False, name_filter: str | None = None):
    """Render thumbnails for all experiments."""
    exp_dir = os.path.join(db_root, "experiments")
    out_dir = os.path.join(STATIC_IMG, "experiments")
    _ensure_dir(out_dir)

    yaml_files = []
    for ext in ("*.yaml", "*.yml"):
        yaml_files.extend(glob.glob(os.path.join(exp_dir, "**", ext), recursive=True))

    ok, fail = 0, 0
    for path in sorted(yaml_files):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            continue
        name = raw.get("label", raw.get("name", os.path.splitext(os.path.basename(path))[0]))
        safe_name = _safe_filename(name)

        if name_filter and _canon(name_filter) != _canon(name):
            continue

        out_path = os.path.join(out_dir, f"{safe_name}.png")
        if not force and os.path.isfile(out_path):
            print(f"  [skip] {safe_name}.png (exists)")
            ok += 1
            continue

        try:
            if render_experiment_thumbnail(path, out_path):
                print(f"  [ok]   {safe_name}.png")
                ok += 1
            else:
                print(f"  [FAIL] {safe_name}: no components found")
                fail += 1
        except Exception as e:
            print(f"  [FAIL] {safe_name}: {e}")
            fail += 1

    print(f"  Experiments: {ok} ok, {fail} failed")


# ----------------------------------------------------------------------- main
def main():
    parser = argparse.ArgumentParser(
        description="Render thumbnails for the KG browser"
    )
    parser.add_argument(
        "--database", default=DEFAULT_DB,
        help=f"Path to tvbo database/ directory (default: {DEFAULT_DB})"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-render even if thumbnail already exists"
    )
    parser.add_argument(
        "--only", choices=["models", "networks", "atlases", "integrators",
                           "coupling_functions", "experiments"],
        help="Render only one category"
    )
    parser.add_argument(
        "--name", help="Render only a specific item (by name or stem)"
    )
    args = parser.parse_args()

    db_root = os.path.abspath(args.database)
    if not os.path.isdir(db_root):
        print(f"Error: database directory not found: {db_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Database: {db_root}")
    print(f"Output:   {STATIC_IMG}")
    print()

    categories = [args.only] if args.only else [
        "models", "networks", "atlases", "integrators", "experiments"
    ]

    if "models" in categories:
        print("Rendering model thumbnails...")
        render_models(db_root, force=args.force, name_filter=args.name)
        print()

    if "networks" in categories:
        print("Rendering network thumbnails...")
        render_networks(db_root, force=args.force, name_filter=args.name)
        print()

    if "atlases" in categories:
        print("Rendering atlas thumbnails...")
        render_atlases(db_root, force=args.force, name_filter=args.name)
        print()

    if "integrators" in categories:
        print("Rendering integrator thumbnails...")
        render_integrators(db_root, force=args.force, name_filter=args.name)
        print()

    if "experiments" in categories:
        print("Rendering experiment thumbnails...")
        render_experiments(db_root, force=args.force, name_filter=args.name)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
