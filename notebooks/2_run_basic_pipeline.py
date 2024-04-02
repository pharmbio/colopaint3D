import os
# import pandas as pd 
import polars as pl
import scanpy as sc
import numpy as np
import typing as tp
import re
from sklearn.decomposition import PCA
# from sklearn.cross_decomposition import PLSCanonical, PLSRegression, CCA
# from sklearn.preprocessing import StandardScaler
# from sklearn.model_selection import cross_validate, cross_val_score
import matplotlib.pyplot as plt
plt.rcParams.update({'figure.max_open_warning': 0})
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms

import os, shutil, glob
import seaborn as sns; sns.set_style("white")
import umap as umap

# import plotnine as gg
# from cytominer_eval import evaluate

os.getcwd()
class basic_pipeline():
    def readData(filename, statmet='SingleCell'):
        df = pl.read_parquet(f'{self.FeatureDir}/{statmet}/{filename}.parquet')
        ##This here is important!!!!!!
        # df=df.select([c for c in df.columns if not is_meta_column(c)])
        # dataNpy = df.to_numpy(df.select(float_columns))
        ##
        onehot_list = df.select(['Metadata_cmpd_cmpdname'])['Metadata_cmpd_cmpdname'].unique().to_list()
        onehot_mapping = {name: i for i, name in enumerate(onehot_list)}
        df = df.with_columns(df['Metadata_cmpd_cmpdname'].map_elements(lambda name: oneHot(name, onehot_mapping)).alias('Metadata_cmpd_one_hot'))
        return df

    # this is code from Dan
    def is_meta_column(
        c:str,
        allowlist:tp.List[str]=["Metadata_Well","Metadata_Barcode","Metadata_AcqID","Metadata_Site"],
        denylist:tp.List[str]=[],
    )->bool:
        """
            allowlist:
                the function will return False for these, no matter if they are metadata or not
            denylist:
                the function will return True for these, no matter if they are metadata or not
        """
        if c in allowlist:
            return False
        if c in denylist:
            return True
        for ex in '''
            Metadata
            ^Count
            ImageNumber
            Object
            Parent
            Children
            Plate
            Well
            Location
            _[XYZ]_
            _[XYZ]$
            BoundingBox
            Phase
            Orientation
            Angle
            Scale
            Scaling
            Width
            Height
            Group
            FileName
            PathName
            URL
            Execution
            ModuleError
            LargeBrightArtefact
            MD5Digest
            RadialDistribution_Frac
            Intensity_
        '''.split():
            if re.search(ex, c):
                return True
        return False


    def oneHot(row, mapping):
        return mapping.get(row, -1)

    def makePCA(df, name='', statmet='SingleCell' , n_components=2):
        dataN=df.select([c for c in df.columns if not is_meta_column(c)]).select(float_columns).to_numpy()
        pca_model = PCA(n_components=2)
        pca_model = pca_model.fit(dataN)
        pcaOut = pca_model.transform(dataN)
        df = df.with_columns([
        pl.Series('pc1', pcaOut[:, 0]),  
        pl.Series('pc2', pcaOut[:, 1])   
        ])

        hue = df['Metadata_cmpd_pathway'].to_list()
        cmap = sns.color_palette("husl", n_colors=len(df['Metadata_cmpd_pathway'].unique().to_list()))

        fig = plt.figure(
        # figsize=[14, 5]
        )
        ax = fig.add_subplot(111)
        ax.set_xlabel('PC 1', fontsize = 10)
        ax.set_ylabel('PC 2', fontsize = 10)
        ax.spines['top'].set_color('w')
        ax.spines['right'].set_color('w')
        ax.spines['left'].set_color('grey')
        ax.spines['bottom'].set_color('grey')
        sns.scatterplot(x=df['pc1'].to_list(),
                        y=df['pc2'].to_list(),
                        palette=cmap, hue=hue,
                        marker='.',
                        ).set(title=f'PCA {name} All'
                    )
        ax.set_facecolor('w')
        ax.get_legend().remove()
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.show()
        plt.close()
        return df

    def makeUMAP(df, name='', statmet='SingleCell' , nn = 200, is_supervised=True, n_components=200, min_dist=0.2, spread= 5, n_epochs=None, metric='cosine', use_pca=True):
        dataN=df.select([c for c in df.columns if not is_meta_column(c)]).select(float_columns).to_numpy()
        umap_model = umap.UMAP(n_neighbors=nn
                            , min_dist=min_dist
                            , spread= spread
                            , n_epochs=n_epochs
                            , metric=metric
                            , n_jobs=-1
                            )
        if use_pca:
            pca_model = PCA(n_components=100)
            pca_model = pca_model.fit(dataN)
            dataN = pca_model.transform(dataN)
            
        if is_supervised:
            umapOut = umap_model.fit_transform(dataN, y=df['Metadata_cmpd_one_hot'].to_list())
            isSup = 'Supervised'
        else:
            umapOut = umap_model.fit_transform(dataN)
            isSup = 'Unsupervised'
        df = df.with_columns([
        pl.Series('umap1', umapOut[:, 0]),  
        pl.Series('umap2', umapOut[:, 1])   
        ])

        hue = df['Metadata_cmpd_pathway'].to_list()
        cmap = sns.color_palette("husl", n_colors=len(df['Metadata_cmpd_pathway'].unique().to_list()))

        fig = plt.figure(
        # figsize=[14, 5]
        )
        ax = fig.add_subplot(111)
        ax.set_xlabel('UMAP 1', fontsize = 10)
        ax.set_ylabel('UMAP 2', fontsize = 10)
        ax.spines['top'].set_color('w')
        ax.spines['right'].set_color('w')
        ax.spines['left'].set_color('grey')
        ax.spines['bottom'].set_color('grey')
        sns.scatterplot(x=df['umap1'].to_list(),
                        y=df['umap2'].to_list(),
                        palette=cmap, hue=hue,
                        marker='.',
                        ).set(title=f'umap {name} All'
                    )
        ax.set_facecolor('w')
        ax.get_legend().remove()
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        # if not os.path.exists(f'{OutputDir}/{statmet}'):
        #     os.makedirs(f'{OutputDir}/{statmet}')
        # plt.savefig(f'{OutputDir}/{statmet}/{name}_umap{nn}nn_{isSup}.png')
        plt.show()
        plt.close()
        return df

    def main(self):
        figformat = 'png'
        dpi = 300
        statarg = 'single'
        self.OutputDir = f'./output/spher_colo52_v1/2_PCAUMAP'
        if not os.path.exists(self.OutputDir): 
            os.makedirs(self.OutputDir)
        self.FeatureDir = './output/spher_colo52_v1/1_FeaturesImages'
        

        filenames = ['PB000137', 'PB000138', 'PB000139', 'PB000140', 'PB000141', 'PB000142']
        statmets = ['SingleCell', 'MedianCell', 'MeanCell']
        for filename in filenames:
            dataNpy, dataL = readData(filename)
            _ = makePCA(dataNpy, dataL, name=filename)
            # _ = makeUMAP(dataNpy, dataL, name=filename)
            _ = makeUMAP(dataNpy, dataL, name=filename, nn=250, is_supervised=True, use_pca=True)
            _ = makeUMAP(dataNpy, dataL, name=filename, nn=300, is_supervised=False, use_pca=True)


if __name__ == "__main__":
    main()