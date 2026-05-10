<div align="center">
  <img src="images/logo.jpg" alt="Plasma Frequency Profile" width="10%" />
  <h1>A note on an inversion algorithm for vertical ionograms for the prediction of plasma frequency profiles</h1>

  A quasi-parabolic approach for inverting ionograms
 
</div>

## Abstract
Building upon the concept of utilizing quasi-parabolic approximations to determine plasma frequency profiles from ionograms, we present a refined multi-quasi-parabolic method for modeling the E and F layers. While a recent study AIP Advances 14 065034 introduced an approach in this direction, we identified several inaccuracies in its mathematical treatment and numerical results. By addressing these issues, we offer a clearer exposition and a more robust algorithm. Our method assumes a parabolic profile for the E layer and approximates the F layer with a series of concatenated quasi-parabolic segments, ensuring continuity and smoothness by matching derivatives at the junctions. Applied to daylight ionograms from the Jicamarca Observatory in Lima, our inversion algorithm demonstrates excellent agreement between the synthetic ionograms generated from our predicted plasma frequency profiles and the original measured data.

Refer to the accompanying [paper](https://arxiv.org/abs/2411.09215) for a more detailed description of the mathematics and algorithms used.
## Results
We used data provided by the Jicamarca Radio Observatory located in Lima, Peru. The data is a .SAO file thus providing all the information of the iongram such as the E and F layer critical frequency and the o-mode trace. We find that the program works for ionograms with E and F layer or daytime ionograms.

On top of predicting the electron density profile or, as well known as plasma frequency profile, we can predict the complete form of the E layer which is usually incomplete in the ionograms. 

<p align="center">
  <img src="images/90.png" alt="Image 1" width="300px"/>
  <img src="images/92.png" alt="Image 2" width="300px"/>

  <img src="images/111.png" alt="Image 1" width="300px"/>
  <img src="images/130.png" alt="Image 2" width="300px"/>
</p>


## How to use
This program expects `.SAO` files, which are commonly used for sharing remote sensing data. These files should be placed in the `/sao_files/` directory. To run the program, simply execute `python3 main.py` in your terminal. As the algorithm solves for the E and F layers, you will see a progress bar. The `avoid_date_list.txt` file lists dates with poor-quality ionograms that should be avoided; otherwise, the program will stop. The final image comparing the results should resemble the examples shown above.
<p align="center">
  <img src="images/progress_bar.png" alt="Image 3" width="95%"/>
</p>

## Watching the reconstruction step by step
`make_animation.py` is a thin driver that mirrors `handle_f_layer`'s loop and saves a side-by-side frame after each QP iteration (left: plasma frequency profile being built, right: original vs reconstructed ionogram). Run it with `python3 make_animation.py`; PNG frames land in `anim_frames/`. Stitch them into a video with:

```bash
ffmpeg -y -framerate 4 -i anim_frames/frame_%03d.png \
  -vf "fps=30,pad=ceil(iw/2)*2:ceil(ih/2)*2" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart inversion_progress.mp4
```

<p align="center">
  <img src="inversion_progress.gif" alt="Reconstruction progress" width="80%"/>
</p>

## References

1. L. Niu, L. Wen, C. Zhou, and M. Deng, "A profile inversion method for vertical ionograms," *AIP Advances*, vol. 14, no. 6, p. 065034, Jun. 2024. doi: [10.1063/5.0208687](https://doi.org/10.1063/5.0208687).

2. J.E. Titheridge, "A new method for the analysis of ionospheric h'(f) records," *Journal of Atmospheric and Terrestrial Physics*, vol. 21, no. 1, pp. 1-12, 1961. doi: [10.1016/0021-9169(61)90185-4](https://doi.org/10.1016/0021-9169(61)90185-4).

3. B. W. Reinisch and X. Huang, "Automatic calculation of electron density profiles from digital ionograms: 3. Processing of bottomside ionograms," *Radio Science*, vol. 18, no. 3, pp. 477-492, 1983. doi: [10.1029/RS018i003p00477](https://doi.org/10.1029/RS018i003p00477).

4. M. H. Reilly and J. D. Kolesar, "A method for real height analysis of oblique ionograms," *Radio Science*, vol. 24, no. 04, pp. 575-583, 1989. doi: [10.1029/RS024i004p00575](https://doi.org/10.1029/RS024i004p00575).

5. J. E. Titheridge, "Direct Manual Calculations of Ionospheric Parameters Using a Single-Polynomial Analysis," *Radio Science*, vol. 2, no. 10, pp. 1237-1253, 1967. doi: [10.1002/rds19672101237](https://doi.org/10.1002/rds19672101237).

6. A. Manjrekar and S. Tulasiram, "Iterative Gradient Correction (IGC) Method for True Height Analysis of Ionograms," *Radio Science*, vol. 58, Nov. 2023, doi: [10.1029/2023RS007808](https://doi.org/10.1029/2023RS007808).

7. K. G. Budden, "The Numerical Solution of the Differential Equations Governing the Reflexion of Long Radio Waves from the Ionosphere. II," *Philosophical Transactions of the Royal Society of London. Series A, Mathematical and Physical Sciences*, vol. 248, no. 939, pp. 45-72, 1955. [Online]. Available: [http://www.jstor.org/stable/91622](http://www.jstor.org/stable/91622).

8. V. K. Forsterling and H. Lassen, "Die Ionisation der Atmosphäre und die Ausbreitung der kurzen elektrischen Wellen (IQ-100 m) über die Erde. III," *Zeitschrift für technis
