#!/usr/bin/env python
"""Bake every asset the landing-page scope plays back, from one tvbo experiment.

Source of truth is ``scripts/landing_experiment.yaml`` — a schema-valid spec that
references ``tvbo:SupHopf`` and ``tvbo:Linear`` by IRI and overrides only the tuned
parameters. From it this script emits ``landing_scope_data.js`` containing:

* the dk_average DK-84 connectome, MNI region centres and the MNI152 cortical
  surface (decimated, with smooth normals) used to draw the brain;
* a **real** global-coupling sweep — each point is an actual ``exp.run("tvboptim")``,
  not a browser reimplementation — subsampled and quantised for playback;
* the generated code for every backend that renders this experiment, so the page
  can show one spec compiled seven ways.

Run from the repo root with an interpreter that can import tvbo::

    $TVBO_SRC/.venv/bin/python scripts/bake_landing_scope.py
    (TVBO_SRC and TVBASE_SRC override the checkout locations; both default to ~/tools)
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parent.parent
TVBO = Path(os.environ.get("TVBO_SRC", "~/tools/tvbo")).expanduser()
DB = TVBO / "tvbo/database"
FSAVG_LABEL = Path(os.environ.get("TVBASE_SRC", "~/tools/tvbase-python")).expanduser() \
    / "tvbase/atlases/fsaverage/label"
FS_RES = "fsaverage5"  # resolved by path; nilearn's fetch API is broken on this venv
SPEC = REPO / "scripts/landing_experiment.yaml"
JS = REPO / "odoo-addons/tvbo/static/src/js"
OUT = JS / "landing_scope_data.js"
OUT_SWEEP = JS / "landing_scope_sweep.js"
OUT_MESH = REPO / "odoo-addons/tvbo/static/src/img/landing_cortex.bin"

# `a` crosses zero, so the grid spans damped oscillation and limit cycles: 20 real runs
SWEEP_A = [-0.05, -0.01, 0.01, 0.05]
SWEEP_G = [0.0, 0.05, 0.12, 0.25, 0.4]
DURATION = 5000.0
TRANSIENT_MS = 2500.0
WINDOW_MS = 2000.0
BRAIN_SAMPLES = 120
TRACE_SAMPLES = 300
TRACE_LABELS = ["L.SFG", "R.PrCG", "L.STG", "R.PCU", "L.LOG", "R.IN"]

# (key, label, language) - filenames come from tvbo
BACKENDS = [
    ("jax", "JAX", "py"),
    ("tvb", "TVB", "py"),
    ("tvboptim", "tvboptim", "py"),
    ("julia", "Julia", "jl"),
    ("networkdynamics", "ND.jl", "jl"),
    ("modelingtoolkit", "MTK.jl", "jl"),
    ("neuroml", "NeuroML", "xml"),
]


def load_experiment():
    """Copy the spec into the tvbo database so its relative bids_dir resolves."""
    from tvbo.classes.experiment import SimulationExperiment

    staged = DB / "experiments/_landing.yaml"
    shutil.copyfile(SPEC, staged)
    try:
        return SimulationExperiment.from_file(str(staged)), staged
    except Exception:
        staged.unlink(missing_ok=True)
        raise


ARRAY_LITERAL = re.compile(r"\[\s*(-?\d+\.\d+)(?:\s*,\s*-?\d+\.?\d*){6,}\s*,?\s*\]")


def elide_arrays(line):
    """Collapse a long numeric literal to its first entry and a count."""
    def sub(m):
        n = len(re.findall(r"-?\d+\.?\d*", m.group(0)))
        return f"[{m.group(1)}, ... {n} values]"
    return ARRAY_LITERAL.sub(sub, line)


def bake_geometry():
    """Node positions, connectome and cortical surface for the landing brain.

    Surface and parcellation are both fsaverage: one template, so there is no
    resampling and no crossing into fs_LR. The surface is midthickness, i.e.
    (pial + white) / 2 — the one tvbase_viewer shows by default. A pial reads
    badly when drawn opaque, because its sulcal openings show through.
    """
    net = yaml.safe_load(open(DB / "networks/tpl-MNI152NLin2009cAsym_rec-avgMatrix_atlas-DesikanKilliany_desc-SCFC_relmat.yaml"))
    labels = [n["label"] for n in net["nodes"]]
    P = np.array([[n["position"][k] for k in "xyz"] for n in net["nodes"]])

    idx = [l.split("\t")[3].strip() for l in
           open(DB / "networks/bids/dk_average/atlas-DesikanKilliany_nodeindices.tsv").read().strip().split("\n")[1:]]
    assert labels == idx
    W = np.loadtxt(DB / "networks/bids/dk_average/atlas-DesikanKilliany_meas-streamlineCount_relmat.dense.tsv", delimiter="\t")
    W = W / W.max()
    np.fill_diagonal(W, 0.0)

    lo, hi = P.min(0), P.max(0)
    span = (hi - lo).max()
    pos3 = (P - (hi + lo) / 2) / span + 0.5

    import nibabel as nib

    import nilearn
    fs = Path(nilearn.__file__).parent / "datasets/data" / FS_RES
    V, Fc, reg = [], [], []
    for side, key in (("lh", "left"), ("rh", "right")):
        pial = nib.load(fs / f"pial_{key}.gii.gz").darrays
        white = nib.load(fs / f"white_{key}.gii.gz").darrays
        v = (np.asarray(pial[0].data, float) + np.asarray(white[0].data, float)) / 2
        f = np.asarray(pial[1].data, np.int64) + sum(len(x) for x in V)
        # fsaverageN is the leading prefix of fsaverage7's vertex order
        annot = nib.freesurfer.read_annot(FSAVG_LABEL / f"{side}.aparc.annot")[0][:len(v)]
        V.append(v); Fc.append(f); reg.append(annot)
    V, Fc = np.concatenate(V), np.concatenate(Fc)
    print(f"  cortex {len(V)}v / {len(Fc)}f ({FS_RES} midthickness)")
    assert len(V) < 65536, "u16 index buffer"

    vreg = surface_regions(np.concatenate(reg), labels, P)
    surf = (V - (hi + lo) / 2) / span + 0.5

    perm = locality_order(Fc, len(surf))
    inv = np.empty(len(surf), np.int64)
    inv[perm] = np.arange(len(surf))
    surf, vreg = surf[perm], vreg[perm]
    # column order is preserved, so the winding survives the renumbering
    Fc = inv[Fc]
    roll = np.argmin(Fc, axis=1)
    Fc = np.stack([Fc[np.arange(len(Fc)), (roll + k) % 3] for k in range(3)], 1)

    tri = np.triu_indices(len(labels), 1)
    keep = np.argsort(W[tri])[::-1][:700]
    edges = [[int(tri[0][k]), int(tri[1][k]), round(float(W[tri][k]), 3)] for k in keep]

    SLO, SHI = -0.75, 1.75
    return {
        "labels": labels,
        "pos": [[round(float(v), 4) for v in p] for p in pos3],
        "edges": edges,
        "meshBin": pack_mesh(surf, Fc, SLO, SHI) + vreg.tobytes(),
        "mesh": {"verts": len(surf), "faces": len(Fc), "range": [SLO, SHI]},
    }


def surface_regions(annot, labels, node_pos):
    """Map fsaverage aparc labels onto connectome node indices.

    The annot's own region names are DK names (`bankssts`, ...); the DK atlas
    terminology carries the same names as `ctx-lh-bankssts` alongside the centroid
    each connectome node sits on, so one centroid match gives the crosswalk. It is
    exact — 84/84 nodes at 0.00 mm.
    """
    import nibabel as nib
    from scipy.spatial import cKDTree

    dseg = yaml.safe_load(open(DB / "atlases/tpl-MNI152NLin2009c_atlas-DesikanKilliany_desc-ranked_dseg.yaml"))
    ents = dseg["terminology"]["entities"]
    enames = list(ents)
    ecent = np.array([[ents[n]["center"][k] for k in "xyz"] for n in enames])
    d, j = cKDTree(ecent).query(node_pos)
    assert d.max() < 0.01, f"node/atlas centroid mismatch ({d.max():.2f} mm)"
    ent2node = {enames[j[i]]: i for i in range(len(node_pos))}

    n_lh = len(annot) // 2
    out = np.zeros(len(annot), np.uint8)
    hit = 0
    for side, sl in (("lh", slice(0, n_lh)), ("rh", slice(n_lh, None))):
        names = [n.decode() for n in
                 nib.freesurfer.read_annot(FSAVG_LABEL / f"{side}.aparc.annot")[2]]
        for i, nm in enumerate(names):
            node = ent2node.get(f"ctx-{side}-{nm}")
            if node is None:
                continue
            m = annot[sl] == i
            out[sl][m] = node
            hit += m.sum()
    print(f"  parcellation: {hit / len(annot):.1%} of vertices in a DK region")
    return out


def locality_order(faces, n_verts):
    """Renumber vertices so mesh neighbours get neighbouring indices.

    fsaverage's own order comes from icosahedral subdivision and is not local: a
    face's second vertex sits on average 3700 indices from its first, so the index
    deltas below are large and near-random. Reverse Cuthill-McKee on the edge graph
    brings that to ~100 and cuts the gzipped mesh by more than half.
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import reverse_cuthill_mckee

    e = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    g = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n_verts, n_verts)).tocsr()
    return reverse_cuthill_mckee((g + g.T).tocsr(), symmetric_mode=True)


def byte_planes(a):
    """Low bytes of every int16, then the high bytes. Deltas this small leave the
    high plane almost constant, which gzip exploits far better than interleaved."""
    b = np.frombuffer(a.astype("<i2").tobytes(), np.uint8)
    return np.concatenate([b[0::2], b[1::2]]).tobytes()


def pack_mesh(surf, faces, lo, hi):
    """Delta-encoded mesh binary: 12-bit vertex coords and face indices relative to
    a running anchor, each stream split into byte planes. Raw u16/u32 buffers are
    noise-like and barely compress at all."""
    q = np.clip(np.round((surf - lo) / (hi - lo) * 4095), 0, 4095).astype(np.int64)
    dv = np.diff(q, axis=0, prepend=np.zeros((1, 3), np.int64))

    f = faces[np.lexsort((faces[:, 2], faces[:, 1], faces[:, 0]))].astype(np.int64)
    anchor = f[:, 0]
    df = np.stack([np.diff(anchor, prepend=0), f[:, 1] - anchor, f[:, 2] - anchor], 1)
    assert np.abs(dv).max() < 32767 and np.abs(df).max() < 32767, "delta overflow"
    return byte_planes(dv) + byte_planes(df)


def b64(arr):
    return base64.b64encode(arr.tobytes()).decode()


def coupling_parameters(exp):
    """Parameters of the network's single coupling; the landing spec declares exactly one."""
    couplings = exp.network.coupling
    one = next(iter(couplings.values())) if isinstance(couplings, dict) else couplings[0]
    return one.parameters


def bake_sweep(exp, labels):
    """One real tvboptim run per grid cell; returns quantised playback frames.

    Cells are stored row-major over (a, G). `sync` is the measured mean pairwise
    correlation of the run, not a model of it.
    """
    lanes = [labels.index(l) for l in TRACE_LABELS]
    step = exp.integration.step_size
    skip = int(TRANSIENT_MS / step)
    span = int(WINDOW_MS / step)
    brain, traces, sync, rms = [], [], [], []
    # bake_code renders from this same object afterwards, so restore these at the end
    cpar = coupling_parameters(exp)
    spec_a = exp.dynamics.parameters["a"].value
    spec_g = cpar["a"].value
    for a in SWEEP_A:
        for g in SWEEP_G:
            exp.dynamics.parameters["a"].value = a
            cpar["a"].value = g
            res = exp.run("tvboptim", duration=DURATION)
            x = np.asarray(res.data)[skip:skip + span, 0, :]

            fc = np.corrcoef(x.T)
            sync.append(round(float(fc[np.triu_indices(len(labels), 1)].mean()), 4))
            rms.append(round(float(x.std()), 5))

            scale = np.percentile(np.abs(x), 99.5) or 1.0
            bi = np.linspace(0, len(x) - 1, BRAIN_SAMPLES).astype(int)
            ti = np.linspace(0, len(x) - 1, TRACE_SAMPLES).astype(int)
            brain.append(np.clip(np.round(np.clip(np.abs(x[bi]) / scale, 0, 1) * 15), 0, 15).astype(np.uint8))
            traces.append(np.clip(np.round((np.clip(x[ti][:, lanes] / scale, -1, 1) + 1) * 127.5), 0, 255).astype(np.uint8))
            print(f"  a={a:<7} G={g:<7} meanFC={sync[-1]:+.3f}  rms={rms[-1]:.4f}")

    exp.dynamics.parameters["a"].value = spec_a
    cpar["a"].value = spec_g

    br = np.concatenate([c.reshape(-1) for c in brain])
    return {
        "sweepA": SWEEP_A,
        "sweepG": SWEEP_G,
        "sync": sync,
        "rms": rms,
        "traceLanes": TRACE_LABELS,
        "brainSamples": BRAIN_SAMPLES,
        "traceSamples": TRACE_SAMPLES,
        "windowMs": WINDOW_MS,
        "brain": b64((br[0::2] << 4 | br[1::2]).astype(np.uint8)),
        "traces": b64(np.concatenate([c.reshape(-1) for c in traces])),
    }


EXT = {"jax": ".py", "tvb": ".py", "tvboptim": ".py",
       "julia": ".jl", "networkdynamics": ".jl", "modelingtoolkit": ".jl", "neuroml": ".nml"}


def bake_code(exp):
    out = []
    prefix = exp.get_experiment_file_prefix()
    for key, label, lang in BACKENDS:
        try:
            src = exp.render_code(format=key)
            src = src if isinstance(src, str) else str(src)
            lines = [elide_arrays(l) for l in re.sub(r"\n{3,}", "\n\n", src).strip("\n").split("\n")]
        except Exception as ex:
            print(f"  {label:22} SKIP {type(ex).__name__}: {str(ex)[:70]}")
            continue
        print(f"  {label:22} {len(lines):>3} lines, widest {max(len(l) for l in lines)}")
        out.append({"key": key, "label": label, "lang": lang,
                    "file": prefix + EXT[key], "lines": lines})
    return out


def main():
    exp, staged = load_experiment()
    try:
        print("geometry:")
        data = bake_geometry()
        print("sweep:")
        data.update(bake_sweep(exp, data["labels"]))
        print("code:")
        data["code"] = bake_code(exp)
        data["spec"] = SPEC.read_text().split("\n")
    finally:
        staged.unlink(missing_ok=True)

    head = ("/* Generated by scripts/bake_landing_scope.py from scripts/landing_experiment.yaml.\n"
            "   Do not edit. The sweep frames are real exp.run(\"tvboptim\") output. */\n")
    # the frames are the bulk of the payload, so they ship separately
    frames = {k: data.pop(k) for k in ("brain", "traces")}
    mesh = data.pop("meshBin")
    OUT.write_text(head + "window.TVBO_SCOPE = " + json.dumps(data, separators=(",", ":")) + ";\n")
    OUT_SWEEP.write_text(
        head + "window.TVBO_SCOPE_FRAMES = " + json.dumps(frames, separators=(",", ":")) + ";\n"
        "window.dispatchEvent(new Event('tvbo-scope-frames'));\n")
    OUT_MESH.write_bytes(mesh)
    for f in (OUT, OUT_SWEEP, OUT_MESH):
        print(f"wrote {f.relative_to(REPO)}  {f.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
