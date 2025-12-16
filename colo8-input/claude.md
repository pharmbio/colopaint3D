# colo8-input: Drug Screening Pipeline

## Philosophy
- Simple, not too much, no bloat
- Error checking later
- One step at a time
- Concise, understandable
- Skip function definitions from the start
- Prioritize visualization over testing

## Folder Structure

```
colo8-input/
├── import-files/           # Input configuration
│   ├── colo8-list.csv     # 8 compounds + 3 references
│   ├── colo8-settings.csv # 308 wells: 240 compounds + 30 refs + 38 DMSO
│   └── patientpainting-SOURCE-dmso.csv
├── PLAID/                  # Constraint optimization
│   ├── organ-colo8-P1.dzn # Experiment parameters
│   ├── plate-design.mzn   # MiniZinc solver
│   └── renamed/           # Final layouts
│       └── colo8-v1-VP-organoid-48h-P1-L1.csv
├── plaid_files/           # PLAID outputs
├── support-files/         # Intermediates
│   └── patientpainting-medchem.csv # Chemical library (32 compounds)
├── idot-protocols/        # Final outputs
│   ├── print_echo.csv    # 455 transfers for liquid handler
│   └── patientpainting.html # Interactive visualization
└── combine_plaid2.ipynb   # Main processing pipeline
```

## Workflow

1. **Define experiment** → `colo8-list.csv` + `colo8-settings.csv`
2. **Run PLAID solver** → optimized plate layout
3. **Process with notebook** → `combine_plaid2.ipynb`
4. **Generate protocol** → `print_echo.csv` for Echo
5. **Visualize** → `patientpainting.html` for QC

## What We Did (2025-12-03)

### 1. Start with colo8-list.csv, colo8-settings.csv
- Have these as input, 
- Make sure settings make sense. #TODO: replace colo8-settings with plate calculator 

### 3. Updated organ-colo8-P1.dzn
- Changed from 35 compounds → 8 compounds
- Updated compound names: colo-002, colo-009, colo-020, colo-028, colo-029, colo-040, colo-041, colo-044
- Set 10 replicates per compound (was 2)
- Set 3 concentrations per compound (was 4)
- Updated controls: dmso (38 reps), ref-001, ref-002, ref-003 (10 reps each at 2.5 µM)
- Verified: 308 total wells !!! This is important for next runs as well. 

### 4. Renamed and cleaned results
- Renamed `P1-1.csv` → `colo8-v1-VP-organoid-48h-P1-L1.csv`

### 5. Adapted combine_plaid2.ipynb for colo8 (2025-12-03 continued)

**Updated colo8-list.csv:**
- Added `Concentration` column: "10 mM" (with space for parsing)
- Added `Solvent` column: "dmso" (lowercase)
- Renamed columns: `code` → `cmpd-code`, `Name` → `ProductName`
- All compounds at 10 mM stock in DMSO

**Created colo8-SOURCE-dmso.csv:**
- Simple hand-pipetting layout: Row A only (A1-A12)
- 8 compounds + 3 references + DMSO = 12 wells total
- All at 10 mM (DMSO at 100 mM)
- Easy linear layout: A1=veliparib, A2=olaparib, A3=fluorouracil, A4=gemcitabine, A5=trifluridine, A6=sn-38, A7=binimetinib, A8=abemaciclib, A9=etoposide, A10=fenbendazole, A11=berberine chloride, A12=dmso

**Notebook changes:**
- **Cell 0178833e**: Load `colo8-list.csv` instead of `patientpainting-medchem.csv`
- **Cell-17**: Skip combination handling (no combinations in colo8)
- **Cell 24e51d11**: Parse Concentration and use Solvent directly
- **Cell 63ba466c**: Load `colo8-SOURCE-dmso.csv`
- Changed all references from "idot" → "echo" (Echo liquid handler)

**Result:** Notebook now processes colo8 compounds without combinations, uses simplified input files

## Key Files

| File | Purpose |
|------|---------|
| `colo8-list.csv` | Compound inventory |
| `colo8-settings.csv` | Experiment design |
| `organ-colo8-P1.dzn` | PLAID input parameters |
| `combine_plaid2.ipynb` | PLAID → Echo protocol |
| `print_echo.csv` | Liquid handler instructions |
| `patientpainting.html` | Visual QC |

## Experiment Summary

- **Platform**: 384-well plate
- **Compounds**: 8 treatment drugs (DNA damage, MAPK, Cell Cycle pathways)
- **Concentrations**: 1.0, 3.0, 10.0 µM
- **Replicates**: 10 per condition
- **References**: etoposide, fenbendazole, berberine chloride at 2.5 µM
- **Controls**: 38 DMSO wells
- **Model**: Organoid (colorectal cancer patient-derived)
- **Timepoint**: 48h

## Additional Optimizations (2025-12-03 continued)

### 6. Fixed stockfinder function (Cell 093f9640)

**Problem**: Echo liquid handler requires volumes in 2.5 nL increments, but original function rejected any stocks that didn't give exact 2.5 nL divisibility. This caused many compounds to fail (return NaN).

**Solution**: Modified stockfinder to:
- Calculate ideal volume for each possible stock
- **Round to nearest 2.5 nL increment** (instead of rejecting)
- Calculate rounding error percentage
- Select stock with minimal error

**Result**:
- 1.0 µM target: 4 nL ideal → rounds to 5 nL (1.25 µM actual, ~25% deviation)
- 3.0 µM target: 12 nL ideal → rounds to 12.5 nL (3.125 µM actual, ~4% deviation)
- 10.0 µM target: 40 nL exact → 40 nL (10.0 µM actual, 0% deviation)

All compounds now have valid stock concentrations assigned!

### 7. Fixed HTML legend duplication (Cell 15bfa347)

**Problem**: Plotly visualization created a scatter trace for every data point, causing each compound name to appear hundreds of times in the legend.

**Solution**:
- Track which compounds have been added to legend using `legend_added` set
- Set `showlegend=False` for subsequent occurrences of same compound
- Only first occurrence of each compound appears in legend

**Result**: Clean legend with each compound listed exactly once.

### 8. Dynamic source plate generation (NEW Cell after 4277a849)

**Problem**:
- Manual source plate only had 10 mM stocks
- Stockfinder now selects 1.0 mM stocks for some compounds (to achieve exact 1.0 µM targets with 40 nL)
- Missing stocks → 80+ "No source found" errors in output

**Solution**: Completely automated source plate generation:

**New cell: Dynamic Source Plate Generator**
```python
# After stockfinder runs and df_w_cmpd is created:
1. Collect all unique (compound, stock_concentration, solvent) combinations
2. Group by solvent (dmso, water, etc.)
3. For each solvent:
   - Create source plate layout (Row A: A1, A2, A3...)
   - Include all needed stock concentrations
   - Always add solvent control at 100% (e.g., DMSO in last well)
   - Save to: import-files/colo8-SOURCE-{solvent}.csv
```

**Key features**:
- ✓ Separate plates per solvent (never mix dmso/water)
- ✓ Solvent name in filename: `colo8-SOURCE-dmso.csv`
- ✓ Automatically includes ALL stocks selected by stockfinder
- ✓ Simple row A layout for easy hand-pipetting
- ✓ No manual source plate creation needed

**Example output** (colo8-SOURCE-dmso.csv):
```
A1: trifluridine [10.0 mM]
A2: etoposide [10.0 mM]
A3: olaparib [10.0 mM]
A4: binimetinib [10.0 mM]
A5: gemcitabine [1.0 mM]     ← Auto-added dilution
A6: fluorouracil [1.0 mM]    ← Auto-added dilution
A7: abemaciclib [1.0 mM]     ← Auto-added dilution
...
A20: dmso [100.0 %]          ← Solvent control
```

### 9. Source plate visualization (NEW Cell after dynamic generation)

**Added**: Interactive table visualization for each generated source plate
- Shows: Well, Compound, Concentration
- Saves to: `echo-protocols/SOURCE-{solvent}-layout.html`
- Provides visual confirmation before pipetting

**Result**: Complete end-to-end automation from PLAID → Echo protocol with zero manual source plate creation!

### Updated Workflow

1. **Define experiment** → `colo8-list.csv` + `colo8-settings.csv`
2. **Run PLAID solver** → optimized plate layout (308 wells)
3. **Process with notebook** → `combine_plaid2.ipynb`
   - Loads PLAID layout
   - Runs stockfinder (selects optimal stocks with 2.5 nL rounding)
   - **Generates source plates dynamically** (NEW!)
   - **Visualizes source plates** (NEW!)
   - Maps compounds to source locations
   - Calculates backfill DMSO
4. **Generate protocol** → `print_echo.csv` for Echo
5. **Visualize** → HTML files for QC
   - Destination plate: `colo8-v1-VP-organoid-48h-P1.html`
   - Source plates: `SOURCE-dmso-layout.html`

### Files Generated Automatically

| File | Generated By | Purpose |
|------|--------------|---------|
| `colo8-SOURCE-dmso.csv` | Notebook (dynamic) | Source plate layout for DMSO compounds |
| `SOURCE-dmso-layout.html` | Notebook (dynamic) | Visual QC of source plate |
| `print_echo.csv` | Notebook | Echo liquid handler protocol |
| `colo8-v1-VP-organoid-48h-P1.html` | Notebook | Interactive destination plate map |

### Key Advantages

1. **No manual source plate creation** - fully automated based on stockfinder results
2. **Handles all stock dilutions** - automatically includes 1.0 mM, 10.0 mM, etc.
3. **Separate plates per solvent** - never mixes solvents (safety!)
4. **2.5 nL rounding** - realistic volumes for Echo liquid handler
5. **Visual confirmation** - HTML tables show exactly what to pipette
6. **Clean legend** - visualization shows each compound once


Notebook Optimization Plan

  Current State:
  - Size: 635 KB
  - Cells: 53 (39 code, 14 markdown)
  - Execution: All cells run sequentially
  - Organization: Monolithic single notebook

  ---
  Optimization Strategy

  1. Modularization (High Impact)

  Problem: All logic in one notebook makes it hard
   to maintain and reuse

  Solution: Extract reusable functions to Python
  modules

  colo8-input/
  ├── src/
  │   ├── __init__.py
  │   ├── stockfinder.py      # stockfinder_idot()
   function
  │   ├── source_plates.py    #
  generate_source_plates()
  │   ├── visualizations.py   # plotly
  visualization functions
  │   └── utils.py            # strip_zeros(), 
  strip_spaces()
  ├── combine_plaid2.ipynb    # Simplified 
  workflow
  └── config.py               # All constants 
  (well_vol_uL, dmso_max_perc, etc.)

  Benefits:
  - ✓ Notebook becomes workflow documentation
  - ✓ Functions can be tested independently
  - ✓ Easier to debug and maintain
  - ✓ Reusable across experiments

  ---
  2. Remove Display Bloat (Medium Impact)

  Problem: Multiple large DataFrame displays
  inflate notebook size

  Current:
  display(df_combined)          # Full 308 row 
  dataframe
  df_combined                   # Duplicate 
  display
  df_w_cmpd                     # Full dataframe
  df_w_cmpd                     # Another 
  duplicate

  Solution:
  # Replace with concise summaries
  print(f"Loaded {len(df_combined)} wells from 
  PLAID")
  print(f"Unique compounds: 
  {df_combined['cmpdname'].nunique()}")
  # Only display when debugging:
  # display(df_combined.head(10))

  Cells to optimize:
  - Cell fedb7227: df_combined → summary only
  - Cell 4277a849: df_w_cmpd → head(10) or summary
  - Cell f93a0300: df_w_cmpd (duplicate) → remove
  - Cell cff9d9d0: number_of_replicates
  (duplicate) → remove
  - Cell 97b75f6a: df_w_cmpd_out → summary only
  - Cell 5d5a97a5: print_echo → head(10) only
  - Cell 58314018: df_source → summary only

  Benefit: Reduce notebook size by ~30-40%

  ---
  3. Optimize Visualizations (Medium Impact)

  Problem: Large plotly figures stored in notebook
   outputs

  Current: Two full plotly figures inline
  - Destination plate visualization
  - Source plate table

  Solution:
  # Don't show in notebook, just save
  fig.write_html(filename)
  print(f"✓ Saved visualization: {filename}")
  # Remove: fig.show()

  Benefit: Faster notebook loading, smaller file
  size

  ---
  4. Streamline Data Flow (Low Impact)

  Problem: Multiple intermediate DataFrames

  Current workflow:
  df_combined → df_combined_w_combinations →
  df_forstockfinder → 
  df_with_stock → df_w_cmpd → df_w_cmpd_out →
  print_echo

  Solution: Reduce intermediate steps where
  possible
  # Example: Combine operations
  df_processed = (df_combined
      .pipe(add_compound_names)
      .pipe(calculate_stocks)
      .pipe(calculate_volumes))

  ---
  5. Configuration Management (Low Impact)

  Problem: Constants scattered throughout notebook

  Current:
  dmso_max_perc = 0.1          # Cell c87ef612
  well_vol_uL = 40             # Cell c87ef612
  exp_name = 'colo8-...'       # Cell c87ef612

  Solution: Centralize in config file or first
  cell
  # config.py or Cell 1
  EXPERIMENT_CONFIG = {
      'name': 'colo8-v1-VP-organoid-48h-P1',
      'well_volume_uL': 40,
      'dmso_max_percent': 0.1,
      'h2o_max_percent': 5,
      'min_volume_nL': 2.5,
      'max_volume_nL': 40,
  }

  ---
  6. Remove Old/Commented Code (Low Impact)

  Problem: Many commented-out sections

  Examples:
  - Cell 964fd228: Commented os.chdir()
  - Cell 897e5e86: Commented display options
  - Cell d64105e7: Large commented section
  - Cell e72f512f: Commented well number
  adjustment

  Solution: Remove or move to archive notebook

  ---
  7. Split into Multiple Notebooks (Optional - 
  High Complexity)

  For very large workflows:

  1_load_and_validate.ipynb    # Import PLAID, 
  validate inputs
  2_calculate_stocks.ipynb     # Run stockfinder, 
  generate source plates  
  3_generate_protocol.ipynb    # Create Echo 
  protocol
  4_visualize_qc.ipynb         # Generate all 
  visualizations

  Pros:
  - Each notebook focused on one task
  - Can run independently
  - Easier debugging

  Cons:
  - More complex workflow
  - Need to manage data passing between notebooks
  - Not recommended for this project (already
  concise)

  ---
  Recommended Implementation Order

  Phase 1: Quick Wins (1-2 hours)

  1. ✓ Remove duplicate DataFrame displays
  2. ✓ Replace large displays with summaries
  3. ✓ Remove commented-out code
  4. ✓ Change visualizations to save-only (no
  show)

  Expected reduction: ~40% file size, 50% faster
  execution

  Phase 2: Modularization (2-4 hours)

  1. ✓ Extract stockfinder function to
  src/stockfinder.py
  2. ✓ Extract source plate generator to
  src/source_plates.py
  3. ✓ Extract visualization functions to
  src/visualizations.py
  4. ✓ Extract utility functions to src/utils.py
  5. ✓ Create config.py for constants

  Expected benefit: Easier maintenance, reusable
  code

  Phase 3: Polish (1 hour)

  1. ✓ Centralize configuration
  2. ✓ Add progress indicators
  3. ✓ Optimize data flow

  ---
  Specific Optimizations for combine_plaid2.ipynb

  High-Priority Changes:

  1. Cell 093f9640 (stockfinder): Extract to
  module
  from src.stockfinder import stockfinder_idot
  2. Cell p5a9qcawhyt (source plate generation):
  Extract to module
  from src.source_plates import
  generate_source_plates
  generate_source_plates(df_w_cmpd, ImportDir,
  exp_name)
  3. Cell 15bfa347 (destination viz): Simplify
  from src.visualizations import create_plate_map
  create_plate_map(df_w_cmpd, OutputDir, exp_name,
   show=False)
  4. Remove display cells:
    - Cell f93a0300 (duplicate df_w_cmpd)
    - Cell cff9d9d0 (duplicate
  number_of_replicates)
  5. Simplify displays:
    - All large DataFrame displays → .head(10) or
  summary stats

  ---
  Expected Results

  | Metric          | Before   | After Phase 1 |
  After Phase 2 |
  |-----------------|----------|---------------|--
  -------------|
  | File size       | 635 KB   | ~380 KB       |
  ~200 KB       |
  | Execution time  | ~2-3 min | ~1-2 min      |
  ~1 min        |
  | Code cells      | 39       | 32            |
  15            |
  | Maintainability | Low      | Medium        |
  High          |
  | Reusability     | None     | Low           |
  High          |

  ---
  Would you like me to implement Phase 1 (quick
  wins) now, or would you prefer to start with
  Phase 2 (modularization)?