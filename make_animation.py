"""
Local-only driver: emit one frame per QP iteration so we can build an mp4
of the reconstruction progress for the website thumbnail.

Mirrors handle_f_layer's loop but saves a side-by-side plot
(left: plasma frequency profile being built, right: original vs reconstructed ionogram)
after every QP step.
"""

import os
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.handle_f_layer import get_qp
from src.handle_special_case_QP1 import find_QP1
from src.get_ionogram import get_ionogram
from src.sao_reader import Ne_prof
from src.utils import (
    check_E_layer_existance,
    L2_ERROR,
    compute_ab,
    generate_values_exp,
    generate_fp_profile,
)

FRAME_DIR = "anim_frames"
SAO_FILE = "sao_files/JI91J_20240511(132).SAO"

BG = "#fbfaf6"
INK = "#1f2933"
MUTED = "#7b8794"
PROFILE = "#e07a5f"
PROFILE_FILL = "#f5d4c5"
ORIG = "#3d5a80"
RECON = "#1f2933"
ACCENT = "#fff495"

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 11,
    "font.weight": 300,
    "axes.titleweight": 400,
    "axes.titlesize": 12,
    "axes.titlecolor": INK,
    "axes.labelweight": 300,
    "axes.labelcolor": MUTED,
    "axes.labelsize": 10,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.facecolor": BG,
    "figure.facecolor": BG,
    "savefig.facecolor": BG,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "grid.color": MUTED,
    "grid.alpha": 0.12,
    "grid.linewidth": 0.6,
    "legend.frameon": False,
    "legend.fontsize": 9,
})


def save_frame(idx, qp_label, error, ori_frq, ori_vh, fp, rh, step, total_steps,
               x_profile_lim=None, y_profile_lim=None):
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 5.2), dpi=160)
    ax_profile, ax_iono = axes

    if fp is not None and len(fp) > 0:
        ax_profile.plot(fp, rh, linewidth=2.4, color=PROFILE,
                        label="reconstructed profile",
                        solid_capstyle="round", solid_joinstyle="round")
        ax_profile.legend(loc="lower right")
    ax_profile.set_xlabel("frequency  (MHz)")
    ax_profile.set_ylabel("height  (km)")
    ax_profile.set_title("plasma frequency profile", loc="left", pad=12)
    ax_profile.grid(True, axis="both")
    if x_profile_lim is not None:
        ax_profile.set_xlim(x_profile_lim)
    if y_profile_lim is not None:
        ax_profile.set_ylim(y_profile_lim)

    ax_iono.plot(ori_frq, ori_vh, "o", color=ORIG, markersize=5,
                 alpha=0.55, mew=0, label="measured")
    if fp is not None and len(fp) > 0:
        s_f, s_vh = get_ionogram(rh, fp, fp)
        ax_iono.plot(s_f, s_vh, "o", color=RECON, markersize=3.2,
                     mew=0, alpha=0.95, label="reconstructed")
    ax_iono.set_xlabel("frequency  (MHz)")
    ax_iono.set_ylabel("virtual height  (km)")
    ax_iono.set_title("ionogram fit", loc="left", pad=12)
    ax_iono.grid(True, axis="both")
    ax_iono.legend(loc="lower right")

    fig.text(0.04, 0.955, qp_label, fontsize=13, color=INK, weight=500)
    if error is not None:
        fig.text(0.04, 0.918, f"L2 error  {error:.3f}", fontsize=10, color=MUTED)

    bar_y = 0.955
    bar_x0 = 0.62
    bar_x1 = 0.96
    frac = step / max(total_steps - 1, 1)
    fig.add_artist(plt.Line2D([bar_x0, bar_x1], [bar_y, bar_y],
                              transform=fig.transFigure,
                              color=MUTED, alpha=0.18, linewidth=2.5,
                              solid_capstyle="round"))
    fig.add_artist(plt.Line2D([bar_x0, bar_x0 + (bar_x1 - bar_x0) * frac],
                              [bar_y, bar_y],
                              transform=fig.transFigure,
                              color=PROFILE, linewidth=2.5,
                              solid_capstyle="round"))
    fig.text(bar_x1, 0.918, f"step  {step + 1} / {total_steps}",
             fontsize=9, color=MUTED, ha="right")

    fig.tight_layout(rect=[0, 0, 1, 0.9])
    fig.savefig(os.path.join(FRAME_DIR, f"frame_{idx:03d}.png"))
    plt.close(fig)


def main():
    if os.path.exists(FRAME_DIR):
        shutil.rmtree(FRAME_DIR)
    os.makedirs(FRAME_DIR, exist_ok=True)

    map_ionograms, dates = Ne_prof(SAO_FILE)

    chosen = None
    for i, date in enumerate(dates):
        frq, vh, foE = map_ionograms[date]
        frq, vh = np.array(frq), np.array(vh)
        if foE is None:
            continue
        if not check_E_layer_existance(frq, vh, foE):
            continue
        chosen = (i, date, frq, vh, foE)
        break

    if chosen is None:
        raise SystemExit("No suitable ionogram with E+F layer found.")

    i, date, frq, vh, foE = chosen
    print(f"Using ionogram: {date}  (foE={foE} MHz, {len(frq)} freq points)")

    epsilon = 1e-10
    last_qp = 10 + (len(frq) - 8) // 4

    # Pass 1: run the algorithm, collect (label, error, fp, rh) per step.
    states = []

    e_snapshots, QP = e_layer_search_with_snapshots(frq, vh, foE, max_snapshots=5)
    for i, snap in enumerate(e_snapshots):
        is_last = i == len(e_snapshots) - 1
        label = "E layer  ·  best fit" if is_last else "E layer  ·  searching"
        states.append((label, snap['error'], snap['fp'].copy(), snap['rh'].copy()))

    foo1 = sorted(
        [find_QP1(original_f=frq, original_vh=vh, QP=QP.copy(), num_points=1)],
        key=lambda x: x[1],
    )[0]
    foo2 = sorted(
        [get_qp(qp_number=1, QP=QP.copy(), data_f=frq, data_r=vh, numt_max=1)],
        key=lambda x: x[1],
    )[0]
    QP, error, _ = foo1 if foo1[1] < foo2[1] else foo2
    states.append(("F layer  ·  QP 1", error,
                   QP['plasma_frequency'].copy(), QP['real_height'].copy()))

    for tmr in range(2, last_qp):
        if error <= epsilon:
            break
        numt_max = 1 if tmr < 10 else 4
        QP, error, _ = get_qp(qp_number=tmr, QP=QP.copy(),
                              data_f=frq, data_r=vh, numt_max=numt_max)
        states.append((f"F layer  ·  QP {tmr}", error,
                       QP['plasma_frequency'].copy(), QP['real_height'].copy()))

    # Drop trailing states whose profile became NaN (algorithm boundary failure).
    while states and (np.isnan(states[-1][2]).any() or np.isnan(states[-1][3]).any()):
        states.pop()

    # Pass 2: lock axes to final ranges and render.
    final_fp = states[-1][2]
    final_rh = states[-1][3]
    fp_min, fp_max = np.nanmin(final_fp), np.nanmax(final_fp)
    rh_min, rh_max = np.nanmin(final_rh), np.nanmax(final_rh)
    fp_pad = max(0.1, 0.04 * (fp_max - fp_min))
    rh_pad = max(5.0, 0.04 * (rh_max - rh_min))
    fp_lim = (max(0.0, fp_min - fp_pad), fp_max + fp_pad)
    rh_lim = (rh_min - rh_pad, rh_max + rh_pad)

    total_steps = 1 + len(states)

    save_frame(0, "input ionogram", None, frq, vh, None, None,
               step=0, total_steps=total_steps,
               x_profile_lim=fp_lim, y_profile_lim=rh_lim)
    for i, (label, err, fp, rh) in enumerate(states):
        save_frame(1 + i, label, err, frq, vh, fp, rh,
                   step=1 + i, total_steps=total_steps,
                   x_profile_lim=fp_lim, y_profile_lim=rh_lim)

    print(f"Wrote {1 + len(states)} frames to {FRAME_DIR}/")


def e_layer_search_with_snapshots(frq, vh, foE, max_snapshots=5):
    """Replicates handle_e_layer's grid search but records best-so-far snapshots
    and returns them subsampled to at most max_snapshots, plus the final QP dict
    matching what handle_e_layer would produce."""
    data_f = frq[frq <= foE]
    data_hv = vh[frq <= foE]
    index = len(data_f)
    eps = 1e-13
    curated_data_f = generate_values_exp(eps, foE - eps, 50, k=3)

    possible_rmE = np.linspace(1.0, 350.0, num=400)
    possible_ymE = np.linspace(1.0, 350.0, num=400)

    best = {'error': 1e9, 'rm': -1, 'ym': -1, 'fp': None, 'rh': None}
    snapshots = []
    for rmE in possible_rmE:
        for ymE in possible_ymE:
            if ymE >= rmE:
                continue
            rh = generate_fp_profile(rmE, ymE, foE,
                                     fp_data_test=curated_data_f,
                                     qp_type='pos_to_neg')
            _, hv = get_ionogram(rh, curated_data_f, data_f - eps)
            err = L2_ERROR(data_hv, hv)
            if err < best['error']:
                best.update(error=err, rm=rmE, ym=ymE,
                            fp=curated_data_f, rh=rh)
                snapshots.append({'error': err,
                                  'fp': curated_data_f.copy(),
                                  'rh': rh.copy()})

    if len(snapshots) > max_snapshots:
        idxs = np.linspace(0, len(snapshots) - 1, max_snapshots).astype(int)
        snapshots = [snapshots[i] for i in idxs]

    fp_add = best['fp'] + eps
    rh_add = best['rh']
    a, b = compute_ab(fc=foE, rb=best['rm'] - best['ym'], ym=best['ym'])
    QP = {'plasma_frequency': fp_add, 'real_height': rh_add,
          'numt': index, 'a_0': a, 'r_m0': best['rm'], 'b_0': b,
          'f_c0': np.sqrt(a)}
    print(f"E LAYER ERROR = {best['error']}  (rm={best['rm']:.2f}, ym={best['ym']:.2f})")
    return snapshots, QP


if __name__ == "__main__":
    main()
