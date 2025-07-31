
import numpy as np


def median_corr_by_group(group, method='spearman' ):
    from scipy.spatial.distance import pdist

    if group.shape[0] < 2:
        return np.nan

    data = group.values
    method = method.lower()
    
    if method == 'spearman':
        # rank along each row, then treat like Pearson
        data = group.rank(axis=1).values
        metric = 'correlation'
    elif method == 'pearson':
        metric = 'correlation'
    elif method == 'cosine':
        metric = 'cosine'
    else:
        raise ValueError(f"Unsupported method '{method}'")

    corr_vals = 1 - pdist(data, metric=metric)

    return np.nanmedian(corr_vals)

def corr_between_non_replicates(df, grouping, method='spearman'):

    shuffled_df = (df
                   .groupby('Metadata_cell_line', group_keys=False,sort=False)
                   .apply(lambda x: x.sample(frac=1, random_state=42))
                   .reset_index(drop=True))  
    
    shuffled_df = shuffled_df.set_index(df.index)
    
    null_corrs = (shuffled_df
                  .groupby(grouping)
                  .apply(lambda g: median_corr_by_group(g, method=method)))

    return null_corrs.to_frame(name='null_corr')

def corr_between_replicates(df, grouping, method='spearman'):
   
    replicate_corrs = (df
                  .groupby(grouping)
                  .apply(lambda g: median_corr_by_group(g, method=method)))

    return replicate_corrs.to_frame(name='corr')

def percent_score(null_dist, corr_dist, how='right'):
    """ # DIRECTLY FROM XXX TODO: 
    Calculates the Percent replicating
    :param null_dist: Null distribution
    :param corr_dist: Correlation distribution
    :param how: "left", "right" or "both" for using the 5th percentile, 95th percentile or both thresholds
    :return: proportion of correlation distribution beyond the threshold
    """
    if how == 'right':
        perc_95 = np.nanpercentile(null_dist, 95)
        above_threshold = corr_dist > perc_95
        return 100 * np.mean(above_threshold.astype(float)), perc_95
    if how == 'left':
        perc_5 = np.nanpercentile(null_dist, 5)
        below_threshold = corr_dist < perc_5
        return 100 * np.mean(below_threshold.astype(float)), perc_5
    if how == 'both':
        perc_95 = np.nanpercentile(null_dist, 95)
        above_threshold = corr_dist > perc_95
        perc_5 = np.nanpercentile(null_dist, 5)
        below_threshold = corr_dist < perc_5
        return 100 * (np.mean(above_threshold.astype(float)) + np.mean(below_threshold.astype(float))), perc_95, perc_5