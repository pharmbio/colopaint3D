"""
Visualization functions for plate layouts and experiment reports
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import StringIO
import sys


def create_plate_visualization(df_w_cmpd, output_dir, exp_name, show=False):
    """
    Create interactive plate map visualization with Plotly.

    Generates an HTML file showing the spatial layout of compounds on the plate
    with color-coded compounds and hover information.

    Parameters
    ----------
    df_w_cmpd : pd.DataFrame
        DataFrame with compound layout including columns:
        - well_number: well column number
        - well_letter: well row letter
        - ProductName: compound name for display
        - CONCuM: concentration in µM
    output_dir : str
        Directory path to save HTML visualization
    exp_name : str
        Experiment name for filename
    show : bool, optional
        If True, display the figure in notebook (default: False)

    Returns
    -------
    str
        Path to saved HTML file

    Notes
    -----
    Output file: {output_dir}/{exp_name}.html

    Features:
    - One dot per compound per well
    - Color-coded by compound
    - Hover shows compound, well, concentration
    - Clean legend (each compound listed once)
    """

    # Assign a unique color per compound using Plotly's built-in palette
    unique_compounds = df_w_cmpd['ProductName'].unique()
    color_palette = px.colors.qualitative.Set3
    color_dict = {compound: color_palette[i % len(color_palette)]
                  for i, compound in enumerate(unique_compounds)}

    # Adjust position if multiple compounds are in the same well
    compound_counts = df_w_cmpd.groupby(['well_number', 'well_letter']).size()
    compound_offsets = {}

    for (well_x, well_y), count in compound_counts.items():
        if count > 1:
            offsets = np.linspace(-0.2, 0.2, count)  # Spread dots in X direction
            compound_offsets[(well_x, well_y)] = offsets
        else:
            compound_offsets[(well_x, well_y)] = [0]  # No offset needed

    # Track which compounds have been added to legend
    legend_added = set()

    # Create scatter plot traces
    scatter_traces = []
    for index, row in df_w_cmpd.iterrows():
        well_x, well_y = row['well_number'], row['well_letter']
        compound_name = row['ProductName']

        # Get color for compound
        color = color_dict.get(compound_name, "gray")

        # Get the offset position for this compound
        offset_index = list(df_w_cmpd[(df_w_cmpd['well_number'] == well_x) &
                                      (df_w_cmpd['well_letter'] == well_y)].index).index(index)
        x_adjusted = int(well_x) + compound_offsets[(well_x, well_y)][offset_index]

        # Only show in legend if this compound hasn't been added yet
        show_in_legend = compound_name not in legend_added
        if show_in_legend:
            legend_added.add(compound_name)

        # Add a scatter trace for each compound
        scatter_traces.append(
            go.Scatter(
                x=[x_adjusted],
                y=[well_y],
                mode="markers",
                marker=dict(size=10, color=color, line=dict(width=1, color="black")),
                name=compound_name,
                showlegend=show_in_legend,
                hoverinfo="text",
                text=f"Compound: {compound_name}<br>Well: {well_y}{well_x}<br>Concentration: {row['CONCuM']} uM"
            )
        )

    # Create the figure
    fig = go.Figure()
    fig.update_layout(width=1600, height=800)

    # Add all scatter traces to the figure
    for trace in scatter_traces:
        fig.add_trace(trace)

    # Customize layout
    fig.update_layout(
        title="Interactive Plate Map with Different Compounds",
        xaxis=dict(title="Well Number", tickmode="array", tickvals=np.arange(1, 25)),
        yaxis=dict(title="Well Letter", tickmode="array", tickvals=sorted(df_w_cmpd['well_letter'].unique())),
        legend_title="Compounds",
        showlegend=True,
        template="plotly_white"
    )

    # Invert the y-axis to match the plate layout
    fig.update_yaxes(autorange="reversed")

    # Sort the y-axis categories alphabetically
    fig.update_yaxes(categoryorder="array", categoryarray=sorted(df_w_cmpd['well_letter'].unique()))

    # Save as html
    output_file = f"{output_dir}/{exp_name}.html"
    fig.write_html(output_file)
    print(f"✓ Saved plate visualization: {output_file}")

    if show:
        fig.show()

    return output_file


def generate_experiment_report(df_w_cmpd, df_backfill, print_echo, df_source,
                               exp_name, well_vol_uL, dmso_max_perc,
                               output_dir, support_dir, plaid_combined_filename,
                               save_pdf=True):
    """
    Generate comprehensive experiment summary report.

    Creates a detailed text report with statistics about compounds, concentrations,
    volumes, and protocol details. Optionally saves as PDF.

    Parameters
    ----------
    df_w_cmpd : pd.DataFrame
        DataFrame with compound layout and volumes
    df_backfill : pd.DataFrame
        DataFrame with DMSO backfill volumes
    print_echo : pd.DataFrame
        Final Echo protocol with all transfers
    df_source : pd.DataFrame
        Source plate layout
    exp_name : str
        Experiment name
    well_vol_uL : float
        Well volume in µL
    dmso_max_perc : float
        Maximum DMSO percentage
    output_dir : str
        Directory for output files
    support_dir : str
        Directory for support files
    plaid_combined_filename : str
        Name of combined PLAID file
    save_pdf : bool, optional
        If True, save report as PDF (default: True)

    Returns
    -------
    str
        Report text content
    """

    # Capture output to both console and string buffer
    class TeeOutput:
        def __init__(self):
            self.terminal = sys.stdout
            self.log = StringIO()

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)

        def flush(self):
            self.terminal.flush()

        def getvalue(self):
            return self.log.getvalue()

    # Start capturing output
    tee = TeeOutput()
    sys.stdout = tee

    print("=" * 80)
    print("ECHO LIQUID HANDLER PROTOCOL GENERATION COMPLETE")
    print("=" * 80)
    print()

    # Experiment Info
    print(f"Experiment Name: {exp_name}")
    print(f"Well Volume: {well_vol_uL} µL")
    print(f"Max DMSO %: {dmso_max_perc}%")
    print()

    # Compound Statistics
    print("=" * 80)
    print("COMPOUND STATISTICS")
    print("=" * 80)
    unique_compounds = df_w_cmpd['cmpdname'].unique()
    total_plates = df_w_cmpd['plateID'].nunique()

    # Categorize compounds using cmpdnum
    df_w_cmpd_temp = df_w_cmpd.copy()
    df_w_cmpd_temp['compound_code'] = df_w_cmpd_temp['cmpdnum'].str.split('_').str[0]

    unique_codes = df_w_cmpd_temp['compound_code'].unique()
    treatment_codes = [c for c in unique_codes if not (c.startswith('ref-') or c == 'dmso')]
    positive_control_codes = [c for c in unique_codes if c.startswith('ref-')]
    negative_control_codes = [c for c in unique_codes if c == 'dmso']

    treatment_compounds = df_w_cmpd_temp[df_w_cmpd_temp['compound_code'].isin(treatment_codes)]['cmpdname'].unique()
    positive_controls = df_w_cmpd_temp[df_w_cmpd_temp['compound_code'].isin(positive_control_codes)]['cmpdname'].unique()
    negative_controls = df_w_cmpd_temp[df_w_cmpd_temp['compound_code'].isin(negative_control_codes)]['cmpdname'].unique()

    print(f"Total plates: {total_plates}")
    print(f"Total unique compounds: {len(unique_compounds)}")
    print(f"  - Treatment compounds: {len(treatment_compounds)}")
    print(f"  - Positive controls: {len(positive_controls)}")
    print(f"  - Negative controls: {len(negative_controls)}")
    print(f"Total treatment wells: {len(df_w_cmpd)}")
    print()

    # Replicate counts with dose information
    print("Replicates per compound (wells × concentrations):")
    for compound in sorted(df_w_cmpd['cmpdname'].unique()):
        compound_data = df_w_cmpd[df_w_cmpd['cmpdname'] == compound]
        total_wells = len(compound_data)
        n_concentrations = compound_data['CONCuM'].nunique()

        if n_concentrations > 1:
            replicates_per_conc = total_wells // n_concentrations
            if total_wells % n_concentrations == 0:
                print(f"  {compound:25s} : {total_wells:3d} wells ({n_concentrations} concentrations, {replicates_per_conc} replicates each)")
            else:
                print(f"  {compound:25s} : {total_wells:3d} wells ({n_concentrations} concentrations, ~{replicates_per_conc} replicates each)")
        else:
            print(f"  {compound:25s} : {total_wells:3d} wells (1 concentration)")
    print()

    # Concentration summary
    print("=" * 80)
    print("CONCENTRATION SUMMARY")
    print("=" * 80)
    conc_summary = df_w_cmpd.groupby(['cmpdname', 'CONCuM', 'stock_unit']).size().reset_index(name='count')
    for compound in sorted(conc_summary['cmpdname'].unique()):
        compound_data = conc_summary[conc_summary['cmpdname'] == compound]
        if compound == 'dmso':
            concs = ', '.join([f"{row['CONCuM']}%" for _, row in compound_data.iterrows()])
        else:
            concs = ', '.join([f"{row['CONCuM']} µM" for _, row in compound_data.iterrows()])
        print(f"  {compound:25s} : {concs}")
    print()

    # DMSO Volume Check
    print("=" * 80)
    print("DMSO VOLUME CHECK (SOLVENT + BACKFILL)")
    print("=" * 80)

    dmso_per_well = df_w_cmpd.groupby('well')['CompVol_nL'].sum().reset_index()
    dmso_per_well.columns = ['well', 'compound_dmso_nL']

    backfill_volumes = df_backfill[['well', 'CompVol_nL']].copy()
    backfill_volumes.columns = ['well', 'backfill_nL']

    dmso_check = dmso_per_well.merge(backfill_volumes, on='well', how='left')
    dmso_check['backfill_nL'] = dmso_check['backfill_nL'].fillna(0)
    dmso_check['total_dmso_nL'] = dmso_check['compound_dmso_nL'] + dmso_check['backfill_nL']

    target_dmso_nL = (dmso_max_perc / 100) * (well_vol_uL * 1000)

    unique_dmso_volumes = dmso_check['total_dmso_nL'].unique()
    print(f"Target DMSO per well: {target_dmso_nL:.1f} nL")
    print(f"Unique DMSO volumes found: {sorted(unique_dmso_volumes)}")
    print(f"Number of unique volumes: {len(unique_dmso_volumes)}")

    tolerance = 0.1
    wells_correct = dmso_check[abs(dmso_check['total_dmso_nL'] - target_dmso_nL) <= tolerance]
    wells_incorrect = dmso_check[abs(dmso_check['total_dmso_nL'] - target_dmso_nL) > tolerance]

    if len(wells_incorrect) == 0:
        print(f"✓ All {len(wells_correct)} wells have correct DMSO volume ({target_dmso_nL:.1f} nL)")
    else:
        print(f"⚠ WARNING: {len(wells_incorrect)} wells have incorrect DMSO volume!")
        for _, row in wells_incorrect.iterrows():
            print(f"  {row['well']}: {row['total_dmso_nL']:.1f} nL (expected {target_dmso_nL:.1f} nL)")
    print()

    # Volume usage per compound × stock
    print("=" * 80)
    print("VOLUME USAGE PER COMPOUND × STOCK CONCENTRATION")
    print("=" * 80)
    volume_summary = df_w_cmpd.groupby(['cmpdname', 'stock_conc_mM', 'stock_unit']).agg({
        'CompVol_nL': 'sum',
        'well': 'count'
    }).reset_index()
    volume_summary.columns = ['Compound', 'Stock_Conc', 'Stock_Unit', 'Total_nL', 'Wells']

    for _, row in volume_summary.sort_values('Compound').iterrows():
        compound = row['Compound']
        stock_conc = row['Stock_Conc']
        stock_unit = row['Stock_Unit'].strip()
        total_nl = row['Total_nL']
        wells = row['Wells']

        if stock_unit == '%':
            stock_str = f"{stock_conc}%"
        else:
            stock_str = f"{stock_conc} {stock_unit}"

        print(f"  {compound:25s} [{stock_str:12s}] : {total_nl:7.1f} nL across {wells:3d} wells")
    print()

    # Source Plate Info
    print("=" * 80)
    print("SOURCE PLATE INFORMATION")
    print("=" * 80)
    print(f"Source plate wells: {len(df_source)}")
    print(f"Unique stock concentrations: {df_source['CONCmM'].nunique()}")
    print()

    # Transfer Statistics
    print("=" * 80)
    print("ECHO PROTOCOL STATISTICS")
    print("=" * 80)
    print(f"Total transfers: {len(print_echo)}")
    print(f"  - Compound transfers: {len(df_w_cmpd)}")
    print(f"  - DMSO backfill transfers: {len(df_backfill)}")
    print()

    print("Transfer volume statistics (nL):")
    print(f"  Min: {print_echo['Transfer Volume'].min():.1f}")
    print(f"  Max: {print_echo['Transfer Volume'].max():.1f}")
    print(f"  Mean: {print_echo['Transfer Volume'].mean():.1f}")
    print(f"  Median: {print_echo['Transfer Volume'].median():.1f}")
    print()

    # Output Files
    print("=" * 80)
    print("OUTPUT FILES GENERATED")
    print("=" * 80)
    print(f"✓ Echo protocol: {output_dir}/print_echo_{exp_name}.csv")
    print(f"✓ Plate visualization: {output_dir}/{exp_name}.html")
    print(f"✓ Combined PLAID data: {support_dir}/{plaid_combined_filename}.csv")
    print()
    print("=" * 80)
    print("READY FOR LIQUID HANDLER")
    print("=" * 80)

    # Restore stdout and get captured text
    sys.stdout = tee.terminal
    report_text = tee.getvalue()

    # Save report as PDF if requested
    if save_pdf:
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_pdf import PdfPages

            pdf_filename = f"{output_dir}/report_{exp_name}.pdf"

            with PdfPages(pdf_filename) as pdf:
                fig = plt.figure(figsize=(8.5, 11))

                fig.text(0.5, 0.96, "Echo Liquid Handler Protocol Report",
                        fontsize=16, weight='bold', ha='center')
                fig.text(0.5, 0.93, exp_name,
                        fontsize=11, ha='center', family='monospace')
                fig.text(0.5, 0.905, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        fontsize=9, ha='center', style='italic')

                fig.add_artist(plt.Line2D([0.1, 0.9], [0.89, 0.89], color='black', linewidth=1))

                fig.text(0.05, 0.87, report_text,
                        fontsize=6.5, family='monospace', verticalalignment='top',
                        transform=fig.transFigure)

                plt.axis('off')
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()

            print(f"✓ Saved report PDF: {pdf_filename}")

        except ImportError:
            print("⚠ Could not save PDF (matplotlib not available)")
        except Exception as e:
            print(f"⚠ Error saving PDF: {e}")

    return report_text
