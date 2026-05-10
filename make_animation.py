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

from src.handle_e_layer import handle_e_layer
from src.handle_f_layer import get_qp
from src.handle_special_case_QP1 import find_QP1
from src.get_ionogram import get_ionogram
from src.sao_reader import Ne_prof
from src.utils import check_E_layer_existance, L2_ERROR

FRAME_DIR = "anim_frames"
SAO_FILE = "sao_files/JI91J_20240511(132).SAO"


def save_frame(idx, qp_label, error, ori_frq, ori_vh, fp, rh, total_steps):
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 5.2), dpi=160)

    ax_profile, ax_iono = axes

    ax_profile.plot(fp, rh, linewidth=3.0, color="orange", label="reconstructed fp profile")
    ax_profile.set_xlabel("Frequency [MHz]")
    ax_profile.set_ylabel("Height [Km]")
    ax_profile.set_title("Plasma frequency profile")
    ax_profile.grid(True, alpha=0.3)
    ax_profile.legend(loc="lower right", fontsize=9)

    s_f, s_vh = get_ionogram(rh, fp, fp)
    ax_iono.plot(ori_frq, ori_vh, "o", color="magenta", markersize=6,
                 alpha=0.4, mew=0, mec="none", label="original ionogram")
    ax_iono.plot(s_f, s_vh, "s", markersize=6, mew=0.6, mec="black",
                 mfc="none", label="reconstructed ionogram")
    ax_iono.set_xlabel("Frequency [MHz]")
    ax_iono.set_ylabel("Virtual height [Km]")
    ax_iono.set_title("Ionogram fit")
    ax_iono.grid(True, alpha=0.3)
    ax_iono.legend(loc="lower right", fontsize=9)

    fig.suptitle(f"{qp_label}   |   L2 error = {error:.3f}", fontsize=12)
    fig.tight_layout()
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

    QP = handle_e_layer(frq=frq, vh=vh, foE=foE)
    save_frame(0, "E layer (QP0)",
               L2_ERROR(vh[: QP['numt']],
                        get_ionogram(QP['real_height'], QP['plasma_frequency'],
                                     frq[: QP['numt']] - 1e-13)[1]),
               frq, vh, QP['plasma_frequency'], QP['real_height'], total_steps=10)

    foo1 = sorted(
        [find_QP1(original_f=frq, original_vh=vh, QP=QP.copy(), num_points=1)],
        key=lambda x: x[1],
    )[0]
    foo2 = sorted(
        [get_qp(qp_number=1, QP=QP.copy(), data_f=frq, data_r=vh, numt_max=1)],
        key=lambda x: x[1],
    )[0]
    QP, error, _ = foo1 if foo1[1] < foo2[1] else foo2
    save_frame(1, "F layer QP 1", error, frq, vh,
               QP['plasma_frequency'], QP['real_height'], total_steps=10)

    frame_idx = 2
    epsilon = 1e-10
    last_qp = 10 + (len(frq) - 8) // 4
    for tmr in range(2, last_qp):
        if error <= epsilon:
            break
        numt_max = 1 if tmr < 10 else 4
        QP, error, _ = get_qp(qp_number=tmr, QP=QP.copy(),
                              data_f=frq, data_r=vh, numt_max=numt_max)
        save_frame(frame_idx, f"F layer QP {tmr}", error, frq, vh,
                   QP['plasma_frequency'], QP['real_height'],
                   total_steps=last_qp)
        frame_idx += 1

    print(f"Wrote {frame_idx} frames to {FRAME_DIR}/")


if __name__ == "__main__":
    main()
