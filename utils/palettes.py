"""One pathway colour and one pathway number, shared by every figure.

Colours and numbers were previously rebuilt inside each notebook. The colours agreed
by coincidence — every notebook happened to declare the same list in the same order —
but the *numbers* did not: ``plot_embedding`` numbered whatever pathways survived grit
filtering in that panel, so "5" meant DNA Damage in one panel and something else in the
next. Both now come from here.

    from utils.palettes import PATHWAY_COLOURS, pathway_numbers

Two orderings are in play, and they are deliberately different:

* **Colour** follows ``_COLOUR_ORDER`` — the order the notebooks declared, which is what
  assigns MAPK the first tab20 blue and so on. Changing it would recolour the published
  figures, so it is fixed here rather than re-derived.
* **Number** follows ``PATHWAY_ORDER`` — alphabetical with "Others" last, which is the
  numbering the published legends use (1 Angiogenesis … 13 Others).
"""
from __future__ import annotations

__all__ = ["PATHWAY_ORDER", "PATHWAY_COLOURS", "pathway_numbers"]

# Order that assigns the colours. Do not reorder: it is what the published figures used.
_COLOUR_ORDER = [
    "MAPK", "Cell Cycle", "DNA Damage", "PI3K/Akt/mTOR", "Epigenetics",
    "Stem Cells & Wnt", "Angiogenesis", "Protein Tyrosine Kinase", "Apoptosis",
    "JAK/STAT", "Cytoskeletal Signaling", "TGF-beta/Smad", "Others", "Proteases",
]

# Order that assigns the legend numbers, as printed in the paper.
PATHWAY_ORDER = [
    "Angiogenesis", "Apoptosis", "Cell Cycle", "Cytoskeletal Signaling", "DNA Damage",
    "Epigenetics", "MAPK", "PI3K/Akt/mTOR", "Proteases", "Protein Tyrosine Kinase",
    "Stem Cells & Wnt", "TGF-beta/Smad", "Others",
]


def _build_colours() -> dict:
    import seaborn as sns
    return dict(zip(_COLOUR_ORDER, sns.color_palette("tab20", len(_COLOUR_ORDER))))


PATHWAY_COLOURS = _build_colours()


def pathway_numbers(present=None) -> dict:
    """Map pathway -> legend number, the same in every panel.

    ``present`` is ignored for numbering — that is the point. A pathway keeps its
    number whether or not it survives grit filtering in a given panel, so the same
    number never means two different things across Fig 4a-d or Suppl 4a-d. Anything
    seen in the data but absent from PATHWAY_ORDER (e.g. JAK/STAT) is appended after
    it rather than silently dropped.
    """
    numbers = {p: i for i, p in enumerate(PATHWAY_ORDER, start=1)}
    # `present` is often a numpy array, where a bare truth test raises
    if present is not None and len(present):
        extra = [p for p in sorted(set(present)) if p not in numbers]
        for i, p in enumerate(extra, start=len(numbers) + 1):
            numbers[p] = i
    return numbers
