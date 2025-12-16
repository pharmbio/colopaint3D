"""
Stock concentration optimization for Echo liquid handler
Finds optimal stock concentrations considering volume constraints and rounding
"""


def stockfinder(x_uM, max_stock, solvent, stock_unit,
                dmso_max_perc, h2o_max_perc, well_vol_uL):
    """
    Calculate optimal stock concentration for Echo liquid handler dispensing.

    This function finds the best stock concentration to use for achieving a target
    concentration, considering:
    - Echo's 2.5 nL volume increment constraint
    - Maximum solvent percentage limits
    - Available stock concentrations
    - Rounding error minimization

    Parameters
    ----------
    x_uM : float
        Target final concentration in µM (or % for DMSO/water controls)
    max_stock : float
        Maximum available stock concentration in mM (or % for solvents)
    solvent : str
        Solvent type: 'dmso', 'water', or other
    stock_unit : str
        Unit of stock concentration: ' mM', ' %', or ' mg/mL'
    dmso_max_perc : float
        Maximum allowed DMSO percentage in well (e.g., 0.1 for 0.1%)
    h2o_max_perc : float
        Maximum allowed water percentage in well (e.g., 5 for 5%)
    well_vol_uL : float
        Working volume in well in µL (e.g., 40)

    Returns
    -------
    list
        [selected_stock_conc, available_stocks] where:
        - selected_stock_conc: optimal stock concentration (mM or %)
        - available_stocks: list of all available stock concentrations
        Returns [None, None] if no valid stock found

    Notes
    -----
    Volume calculation:
        v1 * c1 = v2 * c2
        volume_stock (nL) * conc_stock (mM) = volume_dest (µL) * conc_final (µM)

    Echo constraints:
        - Minimum volume: 2.5 nL
        - Volume must be multiple of 2.5 nL
        - Maximum volume: limited by solvent percentage

    Examples
    --------
    >>> stockfinder(10.0, 10.0, 'dmso', ' mM', 0.1, 5, 40)
    [10.0, [10.0, 1.0, 0.1, 0.01, 0.001, 0.0001]]

    >>> stockfinder(1.0, 10.0, 'dmso', ' mM', 0.1, 5, 40)
    [1.0, [10.0, 1.0, 0.1, 0.01, 0.001, 0.0001]]
    """

    # Determine maximum solvent percentage based on solvent type
    if solvent == 'dmso':
        max_perc = dmso_max_perc
    elif solvent == 'water':
        max_perc = h2o_max_perc
    else:
        max_perc = 0.001  # Unknown solvent, restrict severely

    # Define available stock concentrations (from highest to lowest)
    availstocks_mM = [max_stock, 1.0, 0.1, 0.01, 0.001, 0.0001]

    # Echo volume constraints
    minV1_nl = 2.5  # Minimum volume Echo can dispense
    maxV1_nl = (max_perc / 100) * (well_vol_uL * 1000)  # Max volume before exceeding solvent limit

    stock_unit = stock_unit.strip()

    # Calculate concentration range based on stock unit
    if stock_unit == 'mM':
        # Standard calculation for compounds in mM
        c1_low = (well_vol_uL * x_uM) / maxV1_nl
        c1_high = (well_vol_uL * x_uM) / minV1_nl
    elif stock_unit == '%':
        # For percentage-based stocks (DMSO, water controls)
        x_uM = x_uM * 1000  # Convert
        c1_low = 100  # Always use 100% stock
        c1_high = 100
    elif stock_unit == 'mg/mL':
        # For mg/mL stocks, expand available concentrations
        availstocks_mM = [max_stock, 5.0, 2.5, 1.0, 0.1, 0.01, 0.001, 0.0001]
        c1_low = (well_vol_uL * x_uM) / maxV1_nl
        c1_high = (well_vol_uL * x_uM) / minV1_nl
    else:
        # Unknown stock unit
        return [None, None]

    # Find possible stock concentrations within calculated range
    possible_stocks = [i for i in availstocks_mM if i >= c1_low and i <= c1_high]

    # Validate stocks considering 2.5 nL rounding constraint
    # Prefer stocks that minimize rounding error
    valid_stocks = []
    for stock in possible_stocks:
        volume_nL = (well_vol_uL * x_uM) / stock
        rounded_vol = round(volume_nL / 2.5) * 2.5  # Round to nearest 2.5 nL

        # Check if rounded volume is within acceptable range
        if rounded_vol >= minV1_nl and rounded_vol <= maxV1_nl:
            # Calculate rounding error as percentage
            error_pct = abs(volume_nL - rounded_vol) / volume_nL * 100 if volume_nL > 0 else 0
            valid_stocks.append((stock, error_pct))

    # Select the best stock (prefer low error, then high concentration)
    if not valid_stocks:
        return [None, None]
    else:
        # Sort by error (ascending), then by stock concentration (descending)
        valid_stocks.sort(key=lambda x: (x[1], -x[0]))
        highest_stock = valid_stocks[0][0]
        return [highest_stock, availstocks_mM]
