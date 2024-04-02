import tqdm
import polars as pl
import os

PROJECT_ROOT = "/share/data/analyses/benjamin/Single_cell_project_rapids/grit_parquet/"

def main():
    mad_norm_df = pl.read_parquet('/share/data/analyses/benjamin/Single_cell_project_rapids/sc_profiles_normalized.parquet')
    mad_norm_df = mad_norm_df.filter(pl.col('Metadata_Plate') != "P101384") 
    plates = list(mad_norm_df["Metadata_Plate"].unique())
    load_grit_data(PROJECT_ROOT, plates)


def load_grit_data(folder, plates):
    """
    Processes Parquet files in the given folder based on whether their filenames contain 
    any of the strings in identifier_list. Merges 'Feature' and 'Metric' data based on 
    a specific column and concatenates with 'Control' data.

    :param folder_path: Path to the folder containing Parquet files.
    :param identifier_list: List of strings to be searched in the file names.
    :param merge_column: Column name on which to merge 'Feature' and 'Metric' data.
    :return: Combined Polars DataFrame.
    """
    feature_dfs = []
    metric_dfs = []

    # Iterate over files in the directory
    for plate in tqdm.tqdm(plates):
        file_names = [file for file in os.listdir(folder) if plate in file]
        if len(file_names) == 0:
            print(f"Plate {plate} not found")
            continue
        #file_paths = [os.path.join(folder, file_name) for file_name in file_names]
                # Process based on file type
        for i in file_names:
            file_path = os.path.join(folder, i)
            if "sc_features" in i:
                feature_dfs.append(pl.read_parquet(file_path))
                #feature_df = pl.read_parquet(i) if feature_df is None else feature_df.vstack(pl.read_parquet(i))
            elif "sc_grit" in i:
                metric_dfs.append(pl.read_parquet(file_path).drop("comp"))
                #metric_df = pl.read_parquet(i).drop("comp") if metric_df is None else metric_df.vstack(pl.read_parquet(i).drop("comp"))
    
    feature_df = pl.concat(feature_dfs)
    metric_df = pl.concat(metric_dfs).unique(subset=["Metadata_Cell_Identity"]).unique(subset=["Metadata_Cell_Identity"])
    # Merge Feature and Metric DataFrames
    merged_df = feature_df.join(metric_df, on="Metadata_Cell_Identity", how= "inner")
    # Concatenate Control DataFrames and merge with the above
    #final_df = pl.concat([merged_df, control_dfs])
    #.unique(subset = ["Metadata_Cell_Identity"])
    merged_df.write_parquet(os.path.join(PROJECT_ROOT, "sc_grit_FULL.parquet"))
    #return merged_df


if __name__ == "__main__":
    main()