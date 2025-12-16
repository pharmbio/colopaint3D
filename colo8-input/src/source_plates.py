"""
Dynamic source plate generation based on stockfinder results
Automatically creates source plate layouts for Echo liquid handler
"""

import pandas as pd


def generate_source_plates(df_w_cmpd, support_dir, exp_prefix):
    """
    Dynamically generate source plates based on stocks selected by stockfinder.

    Creates separate source plates for each solvent (DMSO, water, etc.) with:
    - All unique compound × stock concentration combinations
    - Simple row A layout for easy hand-pipetting
    - Solvent control at 100% in the last well

    Parameters
    ----------
    df_w_cmpd : pd.DataFrame
        DataFrame with compound information including columns:
        - cmpdname: compound name
        - stock_conc_mM: stock concentration selected by stockfinder
        - solvent: solvent type ('dmso', 'water', etc.)
        - stock_unit: unit of stock concentration
    support_dir : str
        Directory path to save source plate CSV files
    exp_prefix : str
        Experiment prefix for filename (e.g., 'colo8', 'exp1')

    Returns
    -------
    dict
        Dictionary mapping solvent names to source plate DataFrames
        {solvent_name: df_source_plate}

    Notes
    -----
    Output files are saved as:
        {support_dir}/{exp_prefix}-SOURCE-{solvent}.csv

    Source plate layout:
        - Well A1, A2, A3, ... for each unique compound × stock combination
        - Last well: solvent control at 100%

    Examples
    --------
    >>> source_plates = generate_source_plates(df_w_cmpd, 'support-files', 'exp1')
    >>> # Creates: support-files/exp1-SOURCE-dmso.csv
    >>> # Creates: support-files/exp1-SOURCE-water.csv (if water compounds exist)
    """

    print("=" * 70)
    print("GENERATING SOURCE PLATES DYNAMICALLY")
    print("=" * 70)

    # Collect unique (compound, stock_concentration, solvent) combinations
    df_stocks_needed = df_w_cmpd[['cmpdname', 'stock_conc_mM', 'solvent', 'stock_unit']].copy()
    df_stocks_needed = df_stocks_needed.dropna(subset=['stock_conc_mM'])  # Remove any NaN stocks
    df_stocks_needed = df_stocks_needed.drop_duplicates()

    # Group by solvent
    solvents = df_stocks_needed['solvent'].unique()

    source_plates = {}

    for solvent_name in solvents:
        if pd.isna(solvent_name):
            continue

        print(f"\n--- Generating source plate for solvent: {solvent_name} ---")

        # Get all stocks for this solvent
        df_solvent_stocks = df_stocks_needed[df_stocks_needed['solvent'] == solvent_name].copy()

        # Create source plate layout
        source_rows = []
        well_idx = 1

        for idx, row in df_solvent_stocks.iterrows():
            compound = row['cmpdname']
            stock_conc = row['stock_conc_mM']
            stock_unit = row['stock_unit'].strip()

            # Generate well location (A1, A2, A3, ...)
            well_letter = 'A'
            well_number = well_idx
            well_padded = f"{well_letter}{str(well_number).zfill(2)}"
            well_simple = f"{well_letter}{well_number}"

            source_rows.append({
                'sourceID': f'source_{solvent_name}',
                'well_original': well_padded,
                'well_source': well_padded,
                'Compound': compound,
                'CONCmM': stock_conc,
                'well_letter': well_letter,
                'well_number': well_number,
                'well': well_simple
            })

            print(f"  {well_simple}: {compound} [{stock_conc} {stock_unit}]")
            well_idx += 1

        # Always add the solvent control at the end (e.g., DMSO at 100%)
        if solvent_name == 'dmso':
            control_conc = 100.0  # 100% for DMSO
        elif solvent_name == 'water':
            control_conc = 100.0  # 100% for water
        else:
            control_conc = 100.0

        well_letter = 'A'
        well_number = well_idx
        well_padded = f"{well_letter}{str(well_number).zfill(2)}"
        well_simple = f"{well_letter}{well_number}"

        source_rows.append({
            'sourceID': f'source_{solvent_name}',
            'well_original': well_padded,
            'well_source': well_padded,
            'Compound': solvent_name,
            'CONCmM': control_conc,
            'well_letter': well_letter,
            'well_number': well_number,
            'well': well_simple
        })

        print(f"  {well_simple}: {solvent_name} [{control_conc} %] (solvent control)")

        # Create DataFrame
        df_source_plate = pd.DataFrame(source_rows)

        # Add cmpd_w_stock column for matching
        df_source_plate['cmpd_w_stock'] = df_source_plate['Compound'] + "[" + df_source_plate['CONCmM'].astype(str) + "]"

        # Save to file
        source_filename = f"{support_dir}/{exp_prefix}-SOURCE-{solvent_name}.csv"
        df_source_plate.to_csv(source_filename, index=False)
        print(f"\n✓ Saved: {source_filename}")
        print(f"  Total wells: {len(source_rows)}")

        source_plates[solvent_name] = df_source_plate

    print("\n" + "=" * 70)
    print("SOURCE PLATE GENERATION COMPLETE")
    print("=" * 70)

    return source_plates