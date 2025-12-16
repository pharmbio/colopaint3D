"""
Configuration file for drug screening pipeline
Centralized constants and experiment parameters
"""


class ExperimentConfig:
    """
    Configuration class for Echo liquid handler experiments.

    Attributes
    ----------
    exp_name : str
        Experiment identifier (e.g., 'colo8-v1-VP-organoid-48h-P1')
    well_vol_uL : float
        Working volume in wells in µL
    dmso_max_perc : float
        Maximum allowed DMSO percentage in well
    h2o_max_perc : float
        Maximum allowed water percentage in well
    max_volume_uL : float
        Maximum volume for Echo dispensing in µL
    duplication_factor : int
        Plate duplication factor (for multiple replicates)

    Directory Paths
    ---------------
    output_dir : str
        Directory for Echo protocols and visualizations
    support_dir : str
        Directory for intermediate files
    import_dir : str
        Directory for input files
    plaid_folder : str
        Directory containing PLAID optimization results

    Echo Hardware Settings
    ----------------------
    min_volume_nL : float
        Minimum volume Echo can dispense (nL)
    volume_increment_nL : float
        Volume increment for Echo (must be multiple of this)
    source_plate_type : str
        Echo source plate type identifier
    dest_plate_type : str
        Echo destination plate type identifier
    dest_well_x_offset : int
        Destination well X offset (µm)
    dest_well_y_offset : int
        Destination well Y offset (µm)
    """

    def __init__(self, exp_name):
        """
        Initialize experiment configuration.

        Parameters
        ----------
        exp_name : str
            Experiment name/identifier
        """
        # Experiment identifier
        self.exp_name = exp_name

        # Volume parameters
        self.well_vol_uL = 40  # Working volume in wells
        self.dmso_max_perc = 0.1  # Max DMSO % before toxicity
        self.h2o_max_perc = 5  # Max water % (arbitrary, less harmful than DMSO)
        self.max_volume_uL = 70  # Allow for variation

        # Plate duplication
        self.duplication_factor = 1

        # Directory paths
        self.output_dir = "echo-protocols"
        self.support_dir = "support-files"
        self.import_dir = "import-files"
        self.plaid_folder = "plaid_files"

        # Echo hardware constraints
        self.min_volume_nL = 2.5  # Minimum Echo dispense volume
        self.volume_increment_nL = 2.5  # Echo volume must be multiple of 2.5 nL

        # Echo plate types
        self.source_plate_type = "384PP_DMSO2"
        self.dest_plate_type = "Corning_384w_3784"

        # Echo well offsets (in micrometers)
        self.dest_well_x_offset = 1050
        self.dest_well_y_offset = -1050

    def to_dict(self):
        """
        Convert configuration to dictionary.

        Returns
        -------
        dict
            Configuration as key-value pairs
        """
        return {
            'exp_name': self.exp_name,
            'well_vol_uL': self.well_vol_uL,
            'dmso_max_perc': self.dmso_max_perc,
            'h2o_max_perc': self.h2o_max_perc,
            'max_volume_uL': self.max_volume_uL,
            'duplication_factor': self.duplication_factor,
            'output_dir': self.output_dir,
            'support_dir': self.support_dir,
            'import_dir': self.import_dir,
            'plaid_folder': self.plaid_folder,
            'min_volume_nL': self.min_volume_nL,
            'volume_increment_nL': self.volume_increment_nL,
            'source_plate_type': self.source_plate_type,
            'dest_plate_type': self.dest_plate_type,
            'dest_well_x_offset': self.dest_well_x_offset,
            'dest_well_y_offset': self.dest_well_y_offset,
        }

    def __repr__(self):
        """String representation of configuration."""
        return f"ExperimentConfig(exp_name='{self.exp_name}')"

    def print_summary(self):
        """Print configuration summary."""
        print("=" * 70)
        print("EXPERIMENT CONFIGURATION")
        print("=" * 70)
        print(f"Experiment: {self.exp_name}")
        print(f"Well volume: {self.well_vol_uL} µL")
        print(f"Max DMSO: {self.dmso_max_perc}%")
        print(f"Max H2O: {self.h2o_max_perc}%")
        print(f"Echo min volume: {self.min_volume_nL} nL")
        print(f"Echo volume increment: {self.volume_increment_nL} nL")
        print()
        print("Directories:")
        print(f"  Output: {self.output_dir}")
        print(f"  Support: {self.support_dir}")
        print(f"  Import: {self.import_dir}")
        print(f"  PLAID: {self.plaid_folder}")
        print("=" * 70)
