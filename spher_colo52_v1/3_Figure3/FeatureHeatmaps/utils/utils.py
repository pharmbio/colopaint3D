import os
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd


def find_project_root(marker='.git'):
    """Find the project root by walking up to a directory containing the marker (e.g., .git)."""
    path = Path.cwd()
    while not (path / marker).exists() and path != path.parent:
        path = path.parent
    return path if (path / marker).exists() else None

def apply_defaults(set_cwd=False, marker='.git'):
    """Apply consistent plot settings; optionally set cwd to project root."""
    sns.set_style("white")
    plt.rcParams['pdf.fonttype'] = 42
    plt.rcParams['ps.fonttype'] = 42

    if set_cwd:
        root = find_project_root(marker=marker)
        if root:
            os.chdir(root)
            print(f"[cwd set] {root}")
        else:
            print("[cwd not changed] Project root not found.")

def pDose(x):
    return(-np.log10(1e-6*x))


def list_features(df):
    return [c for c in df.columns if not c.startswith("Metadata")]

def list_metadata(df):
    return [c for c in df.columns if c.startswith("Metadata")]

def get_featuredata(df):
    """Return DataFrame of numeric, non-metadata feature columns."""
    feature_cols = list_features(df)
    assert all(np.issubdtype(df[c].dtype, np.number) for c in feature_cols), \
        "Non-numeric columns found in feature data"
    return df[feature_cols]

def get_metadata(df):
    return df[list_metadata(df)]

def fill_missing_values_with_median(df, cell_line, ListOfFeatures):
    # Select only the cell line of interest
    df2 = df.loc[df['Metadata_cell_line'] == cell_line, ListOfFeatures]

    # Find missing columns
    missing_columns = df2.isna().sum()
    missing_columns = missing_columns[missing_columns > 0]

    # Replace missing values with the median of that feature
    for feature in missing_columns.index:
        feature_median = df2[feature].median()
        df2.loc[df2[feature].isna(), feature] = feature_median

    # Replace the original dataframe with the new one
    df.loc[df['Metadata_cell_line'] == cell_line, ListOfFeatures] = df2

def define_colors():
    
    ## Define color-map for controls
    label_order_controls = [
        'water', 'water+', 'dmso', 'sorb', 'flup', 'fenb', 'etop', 'stau', 'Bortez'
    ]
    color_dict_controls = {
        'water': '#66c2a5',
        'water+': '#66c2a5',
        'dmso': '#b3b3b3',
        'sorb': '#e5c494',
        'flup': '#a6d854',
        'fenb': '#ffd92f',
        'etop': '#fc8d62',
        'stau': '#8da0cb',
        'Bortez': '#e78ac3'
    }

    ## Define color-map for cell lines
    label_order_cells = [
        'C1488', 'DLD1', 'HT29', 'CACO2', 'COLO205', 'SW620', 'HCT15', 'HCT116'
        ]

    color_dict_cells = {
    'C1488': '#4c72b0',
    'DLD1': '#dd8452',
    'HT29': '#55a868',
    'CACO2': '#c44e52',
    'COLO205': '#8172b3',
    'SW620': '#937860',
    'HCT15': '#da8bc3',
    'HCT116': '#8c8c8c'}

    return label_order_controls, label_order_cells, color_dict_cells, color_dict_controls
