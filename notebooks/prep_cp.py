import polars as pl
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import tqdm
import gc

def main():
    meta_features = ['Metadata_Plate',
                    'Metadata_cmpdName',
                    'Metadata_Well',
                    'Metadata_Site',
                    'Location_Center_X_nuclei',
                    'Location_Center_Y_nuclei',
                    'ImageNumber_nuclei',
                    'ObjectNumber_nuclei',
                    'Metadata_AcqID_nuclei',
                    'FileName_CONC_nuclei',
                    'FileName_HOECHST_nuclei',
                    'FileName_ICF_CONC_nuclei',
                    'FileName_ICF_HOECHST_nuclei',
                    'FileName_ICF_MITO_nuclei',
                    'FileName_ICF_PHAandWGA_nuclei',
                    'FileName_ICF_SYTO_nuclei',
                    'FileName_MITO_nuclei',
                    'FileName_PHAandWGA_nuclei',
                    'FileName_SYTO_nuclei',
                    'PathName_CONC_nuclei',
                    'PathName_HOECHST_nuclei',
                    'PathName_ICF_CONC_nuclei',
                    'PathName_ICF_HOECHST_nuclei',
                    'PathName_ICF_MITO_nuclei',
                    'PathName_ICF_PHAandWGA_nuclei',
                    'PathName_ICF_SYTO_nuclei',
                    'PathName_MITO_nuclei',
                    'PathName_PHAandWGA_nuclei',
                    'PathName_SYTO_nuclei']
    

    cols_to_drop = ['Children_cytoplasm_Count_nuclei',
                    'Location_Center_Z_nuclei',
                    'Neighbors_FirstClosestObjectNumber_Adjacent_nuclei',
                    'Neighbors_SecondClosestObjectNumber_Adjacent_nuclei',
                    'Number_Object_Number_nuclei',
                    'Parent_cells_nuclei',
                    'ImageNumber_cells',
                    'Metadata_AcqID_cells',
                    'FileName_CONC_cells',
                    'FileName_HOECHST_cells',
                    'FileName_ICF_CONC_cells',
                    'FileName_ICF_HOECHST_cells',
                    'FileName_ICF_MITO_cells',
                    'FileName_ICF_PHAandWGA_cells',
                    'FileName_ICF_SYTO_cells',
                    'FileName_MITO_cells',
                    'FileName_PHAandWGA_cells',
                    'FileName_SYTO_cells',
                    'PathName_CONC_cells',
                    'PathName_HOECHST_cells',
                    'PathName_ICF_CONC_cells',
                    'PathName_ICF_HOECHST_cells',
                    'PathName_ICF_MITO_cells',
                    'PathName_ICF_PHAandWGA_cells',
                    'PathName_ICF_SYTO_cells',
                    'PathName_MITO_cells',
                    'PathName_PHAandWGA_cells',
                    'PathName_SYTO_cells',
                    'Children_cytoplasm_Count_cells',
                    'Children_nuclei_Count_cells',
                    'Location_Center_Z_cells',
                    'Neighbors_FirstClosestObjectNumber_Adjacent_cells',
                    'Neighbors_SecondClosestObjectNumber_Adjacent_cells',
                    'Number_Object_Number_cells',
                    'Parent_precells_cells',
                    'ImageNumber_cytoplasm',
                    'Metadata_AcqID_cytoplasm',
                    'FileName_CONC_cytoplasm',
                    'FileName_HOECHST_cytoplasm',
                    'FileName_ICF_CONC_cytoplasm',
                    'FileName_ICF_HOECHST_cytoplasm',
                    'FileName_ICF_MITO_cytoplasm',
                    'FileName_ICF_PHAandWGA_cytoplasm',
                    'FileName_ICF_SYTO_cytoplasm',
                    'FileName_MITO_cytoplasm',
                    'FileName_PHAandWGA_cytoplasm',
                    'FileName_SYTO_cytoplasm',
                    'PathName_CONC_cytoplasm',
                    'PathName_HOECHST_cytoplasm',
                    'PathName_ICF_CONC_cytoplasm',
                    'PathName_ICF_HOECHST_cytoplasm',
                    'PathName_ICF_MITO_cytoplasm',
                    'PathName_ICF_PHAandWGA_cytoplasm',
                    'PathName_ICF_SYTO_cytoplasm',
                    'PathName_MITO_cytoplasm',
                    'PathName_PHAandWGA_cytoplasm',
                    'PathName_SYTO_cytoplasm',
                    'Number_Object_Number_cytoplasm',
                    'Parent_cells_cytoplasm',
                    'Parent_nuclei_cytoplasm']

    specs5k_classification_list = pl.read_parquet("/home/jovyan/share/data/analyses/benjamin/Single_cell_supervised/SPECS_MOA/DeepProfiler/datasets/specs5k_compound_list.parquet")
    print("Importing data")
    #specs3k_sc_locations = pl.read_parquet("sc_profiles_classification_specs3k_CellProfiler.parquet")
    #specs3k_sc_features_total = feature_selection_cellprofiler(specs3k_sc_locations, specs5k_classification_list, operation = "clip")
    #specs3k_sc_features_total.write_parquet("/home/jovyan/share/data/analyses/benjamin/Single_cell_supervised/SPECS_MOA/CellProfiler/datasets/specs3k_sc_features.parquet")
    gc.collect()
    specs2k_sc_locations = pl.read_parquet("datasets/sc_profiles_classification_specs2k_CellProfiler.parquet")
    specs2k_sc_features_total = feature_selection_cellprofiler(specs2k_sc_locations, specs5k_classification_list, operation = "clip")
    specs2k_sc_features_total.write_parquet("/home/jovyan/share/data/analyses/benjamin/Single_cell_supervised/SPECS_MOA/CellProfiler/datasets/specs2k_sc_featfix_CP.parquet")
    gc.collect()

    #specs5k_sc_features_total = pl.concat([specs3k_sc_features_total, specs2k_sc_features_total])
    print("Saving to file")
    gc.collect()
    #specs5k_sc_features_total.write_parquet("sc_profiles_classification_specs5k_total.parquet")




import re
import pycytominer as pm

def is_meta_column(c):
    for ex in '''
        Metadata
        ^Count
        ImageNumber
        Object
        Parent
        Children
        Plate
        Well
        location
        Location
        _[XYZ]_
        _[XYZ]$
        Phase
        Scale
        Scaling
        Width
        Height
        Group
        FileName
        PathName
        BoundingBox
        URL
        Execution
        ModuleError
        LargeBrightArtefact
    '''.split():
        if re.search(ex, c):
            return True
    return False

def drop_skew(df, columns_to_check, quantile: float=0.8):
    """
    Drop columns based on skewness threshold from a list of specified columns and
    print the number of columns dropped. Validates that columns exist before processing.

    Parameters:
    - df: The input DataFrame.
    - columns_to_check: A list of column names to check for skewness.
    - quantile: The quantile of skewness to use as a threshold (default is 0.8).

    Returns:
    - A DataFrame with specified skewed columns dropped.
    """
    df = df.to_pandas()
    existing_columns = [col for col in columns_to_check if col in df.columns]
    missing_columns = set(columns_to_check) - set(existing_columns)
    
    if missing_columns:
        print(f"Warning: The following columns do not exist in DataFrame and will be skipped: {missing_columns}")

    initial_col_count = len(df.columns)
    skew = df[existing_columns].skew().abs()
    threshold = skew.quantile(quantile)
    skewed = list(skew[skew > threshold].index)
    final_df = df.drop(columns=skewed)
    final_col_count = len(final_df.columns)

    print(f"Skewness-based method dropped {initial_col_count - final_col_count} columns.")
    out_polars = pl.DataFrame(final_df)
    return out_polars

def drop_low_variance(df, columns_to_check, threshold: float=0.001):
    """
    Drop columns based on variance threshold from a list of specified columns and
    print the number of columns dropped. Validates that columns exist before processing.

    Parameters:
    - df: The input DataFrame.
    - columns_to_check: A list of column names to check for low variance.
    - threshold: The variance threshold below which columns are dropped (default is 0.001).

    Returns:
    - A DataFrame with specified low variance columns dropped.
    """
    df = df.to_pandas()
    existing_columns = [col for col in columns_to_check if col in df.columns]
    missing_columns = set(columns_to_check) - set(existing_columns)
    
    if missing_columns:
        print(f"Warning: The following columns do not exist in DataFrame and will be skipped: {missing_columns}")

    initial_col_count = len(df.columns)
    var = df[existing_columns].var().abs()
    low_variance_cols = list(var[var < threshold].index)
    final_df = df.drop(columns=low_variance_cols)
    final_col_count = len(final_df.columns)

    print(f"Low variance-based method dropped {initial_col_count - final_col_count} columns.")
    out_polars = pl.DataFrame(final_df)
    return out_polars

def drop_low_variance_pl(df, columns_to_check, threshold: float=0.001):
    """
    Drop columns based on variance threshold from a list of specified columns in a Polars DataFrame.

    Parameters:
    - df: The input Polars DataFrame.
    - columns_to_check: A list of column names to check for low variance.
    - threshold: The variance threshold below which columns are dropped.

    Returns:
    - A DataFrame with specified low variance columns dropped.
    """
    # Ensure columns_to_check only contains columns that exist in df
    valid_columns = [col for col in columns_to_check if col in df.columns]
    
    # Initialize a list to keep track of columns to drop
    columns_to_drop = []

    # Iterate over each column to check variance
    for col in valid_columns:
        # Calculate the variance of the column
        variance = df.select(pl.var(pl.col(col)).alias("variance")).to_pandas().iloc[0, 0]

        # If variance is below the threshold, mark the column for dropping
        if variance < threshold:
            columns_to_drop.append(col)

    # Drop the columns with low variance
    df = df.drop(columns_to_drop)

    # Print information about dropped columns
    if columns_to_drop:
        print(f"Dropped {len(columns_to_drop)} columns for low variance: {columns_to_drop}")
    else:
        print("No columns dropped due to low variance.")

    return df


def clip_to_percentiles(df, cols, lower_percentile=1, upper_percentile=99):
    """
    Clip values in the specified columns of the DataFrame to the given percentiles,
    while keeping all columns in the returned DataFrame.

    Parameters:
    - df: The input DataFrame.
    - cols: A list of column names to be processed.
    - lower_percentile: The lower percentile to clip values at (default is 1).
    - upper_percentile: The upper percentile to clip values at (default is 99).

    Returns:
    - A DataFrame with values in the specified columns clipped to the percentiles,
      including all original columns.
    """
    for col in tqdm.tqdm(cols):
        if col not in df.columns:
            print(f"Column {col} does not exist in DataFrame.")
            continue  # Skip non-existent column
        
        # Calculate the percentile values for the column
        #lower_value = df.select(pl.col(col).quantile(lower_percentile / 100.0)).to_numpy()[0,0]
        #upper_value = df.select(pl.col(col).quantile(upper_percentile / 100.0)).to_numpy()[0,0]
        lower_value = -100
        upper_value = 100

        # Create a new column for the clipped values
        #clipped_col = (pl.when(pl.col(col) < lower_value).then(lower_value)
        #                 .when(pl.col(col) > upper_value).then(upper_value)
        #                 .otherwise(pl.col(col)).alias(col))
        # Add the clipped column to the DataFrame

        df = df.with_columns(df[col].clip(lower_value, upper_value).alias(col))
    return df
        

def drop_outliers(df, percentile=99):
    conditions = []
    for col in df.columns:
        if col not in meta_features + extra_features:  # Skip meta and extra features
            p99 = df[col].quantile(percentile / 100.0)
            conditions.append(df[col] <= p99)
    # Combine conditions: row must satisfy all conditions to be retained
    combined_condition = conditions[0]
    for condition in conditions[1:]:
        combined_condition = combined_condition & condition
    return df.filter(combined_condition)




def feature_selection_cellprofiler(normalized_profiles, meta_dat, operation = "clip"):
    meta_df_features = meta_dat.columns
    meta_features = [col for col in normalized_profiles.columns if is_meta_column(col)]
    #normalized_profiles = normalized_profiles.filter(pl.col("Children_cytoplasm_Count_nuclei") > 0).filter(pl.col("Children_cytoplasm_Count_cells") > 0).filter(pl.col('Children_nuclei_Count_cells') > 0).filter(~pl.any_horizontal(pl.all().is_null()))
    normalized_profiles = normalized_profiles.filter(~pl.any_horizontal(pl.all().is_null()))
    print("JOINING")
    normalized_profiles_merge = normalized_profiles.drop(["Metadata_cmpdConc", "moa", "compound_name"]).join(meta_dat.drop("Metadata_cmpdConc"), left_on = ["Metadata_Plate", "Metadata_Well","Metadata_cmpdName", "Metadata_Site"], right_on = ["Metadata_Plate", "Metadata_Well","Metadata_cmpdName", "Metadata_Site"], how ="left")
    blocklist_features = [col for col in normalized_profiles.columns if "Correlation_Manders" in col and "_nuclei" in col] +[col for col in normalized_profiles.columns if "Correlation_RWC" in col and "_nuclei" in col] +[col for col in normalized_profiles.columns if "Granularity_14" in col and "_nuclei" in col] + [col for col in normalized_profiles.columns if "Granularity_15" in col and "_nuclei" in col] +[col for col in normalized_profiles.columns if "Granularity_16" in col and "_nuclei" in col]
    features = [feat for feat in normalized_profiles_merge.columns if feat not in meta_features and feat not in blocklist_features and feat not in meta_df_features]
    extra_features = [feat for feat in normalized_profiles_merge.columns if feat in meta_df_features]
    print("SELECTING FEATURES")
    features_comp = list(set(features + extra_features))
    final_feat_df = normalized_profiles_merge.select(features_comp)
    final_feat_df = final_feat_df.drop('')
    #final_feat_df = drop_skew(final_feat_df, features)
    print("CLIPPING")
    gc.collect()
    print(final_feat_df.shape)
    if operation == 'clip':
        final_features = clip_to_percentiles(final_feat_df, features)
    elif operation == 'drop':
        final_features = drop_outliers(final_feat_df)
    else:
        raise ValueError("Unsupported operation. Choose 'clip' or 'drop'.")
    gc.collect()
    columns_to_drop = [col for col in features if final_features.select(pl.col(col).var()).to_numpy()[0][0] < 0.001]
    print(f"{len(columns_to_drop)} cols to drop!")
# Drop the columns with variance below the threshold
    df_filtered = final_features.drop(columns_to_drop)  

    return df_filtered




if __name__ == '__main__':
    main()
