# Panel checks

Side-by-side renders of regenerated panels against `figures/actual_panels/`, kept so a
claim like "this reproduces the paper" can be looked at rather than taken on trust.
Regenerate any of them by rendering the panel PDF and the matching crop of the published
PNG; they are review aids, not analysis outputs.

| File | Shows |
|---|---|
| `fig3gh_vs_original.png` | Fig 3g/3h reconstruction vs the surviving `AggVsMIP_*.pdf` |
| `fig4ab_features_vs_published.png` | Fig 4a/4b with the filtered (275/308) vs full (474/598) feature set, against the published panels. The filtered set — what `is_meta_column` leaves — is the one that matches |
| `fig5f_PUBLISHED.png` | the published Fig 5f, cropped |
| `fig5f_MINE_current.png` | published above, current reconstruction below |
| `fig5f_conc_experiment.png` | Fig 5f rows at the lowest vs highest grit-passing dose. The highest reproduces the published contrast; the lowest renders nearly white |
