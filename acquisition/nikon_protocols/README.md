# Nikon acquisition protocols

Instrument configuration for the 3D Cell Painting acquisition described in the
paper. These files are included because the adaptive spheroid-finding and
z-detection routine *is* the method being proposed — it is the one part of the
workflow a reader cannot reconstruct from the analysis notebooks.

They are configuration, not data, and contain no local paths, usernames or
machine names (checked before inclusion).

## Files

| File | What it is |
|---|---|
| `Automatic position detection in 4X 2.ga3` | GA3 recipe: locate spheroids in a low-magnification 4× overview and convert them into stage positions for high-magnification imaging |
| `Spheriod_z_detection_derivative.ga3` | GA3 recipe: find the spheroid's z extent from the derivative of an intensity profile, so the z-stack is placed on the object rather than a fixed range |
| `SpheroidDetection.bin` | NIS-Elements JOBS job — the acquisition loop that runs the two recipes above per well |
| `SpheroidDetection_setup.bin` | JOBS setup/configuration accompanying the job |
| `SelectionOC_20230916.xml` | Optical configuration set (UTF-16 XML) — 136 entries, including the five Cell Painting channels and their spheroid-specific variants |

## Optical configurations

The five Cell Painting channels, each with a `_Spheroid` variant tuned for 3D:

| Config | Target |
|---|---|
| `HOECHST_Spheroid` | DNA / nuclei |
| `SYTO_Spheroid` | nucleic acids |
| `PHAandWGA_Spheroid` | membrane / cytoskeleton |
| `MITO_Spheroid` | mitochondria |
| `CONC_Spheroid` | ER / Golgi |

Two further configurations support the adaptive workflow rather than profiling:

- **`4X SYTO`** — low-magnification overview used to find spheroids before
  switching to high magnification.
- **`SYTO_Spheroid_Bounds`** — used by the z-detection recipe to establish the
  spheroid's upper and lower bounds.

Also present: a `Prime BSI Express - DIA:20X Phase` transmitted-light
configuration, and legacy wavelength-named configs (`405-nucleus`, `488-golgi`,
`561-mito`, `640-actin`, `440-er`) retained from earlier 2D work.

## Reusing these

`.bin` and `.ga3` are proprietary NIS-Elements formats and are only meaningful
when loaded into that software. Import the optical configurations from the XML
first, since the JOBS job references configurations by name and will not resolve
them otherwise.

> **TODO before submission:** record the exact **NIS-Elements version** these were
> authored in. The files carry no embedded version string, and without it a reader
> with a different release may not be able to load them. Add the microscope model,
> objectives and camera here too — the XML names a `Prime BSI Express` camera, but
> the paper's methods section is the authority.
