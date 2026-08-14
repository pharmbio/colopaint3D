# Nikon acquisition protocols

Instrument configuration for the 3D Cell Painting acquisition. Included because the
adaptive spheroid-finding and z-detection routine *is* the method being proposed — the one
part of the workflow a reader cannot reconstruct from the notebooks. Configuration, not
data; checked for embedded local paths, usernames and machine names before inclusion.

| File | What it is |
|---|---|
| `Automatic position detection in 4X 2.ga3` | GA3 recipe: find spheroids in a 4× overview, convert to stage positions |
| `Spheriod_z_detection_derivative.ga3` | GA3 recipe: find the spheroid's z extent from an intensity-profile derivative, so the stack is placed on the object |
| `SpheroidDetection.bin` | NIS-Elements JOBS job running both recipes per well |
| `SpheroidDetection_setup.bin` | JOBS setup accompanying the job |
| `SelectionOC_20230916.xml` | Optical configurations (UTF-16), 136 entries |

**Optical configurations.** The five Cell Painting channels each have a `_Spheroid` variant
tuned for 3D: `HOECHST_Spheroid` (DNA), `SYTO_Spheroid` (nucleic acids), `PHAandWGA_Spheroid`
(membrane), `MITO_Spheroid` (mitochondria), `CONC_Spheroid` (ER/Golgi). Two more support the
adaptive workflow: **`4X SYTO`** (low-mag spheroid finding) and **`SYTO_Spheroid_Bounds`**
(z-bounds detection). Also present: a `Prime BSI Express - DIA:20X Phase` transmitted-light
config and legacy wavelength-named configs from earlier 2D work.

**Reuse.** `.bin`/`.ga3` are proprietary NIS-Elements formats. Import the optical
configurations from the XML **first** — the JOBS job references them by name.

> **TODO before submission:** record the **NIS-Elements version** these were authored in
> (the files carry no version string, and a different release may not load them), plus the
> microscope, objectives and camera.
