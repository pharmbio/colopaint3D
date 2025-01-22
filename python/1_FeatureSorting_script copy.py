import os
import pandas as pd 
import polars as pl # like pandas, but much faster
import polars.selectors as cs
import numpy as np
import os, shutil, glob
from random import randint
import re, math
import datetime
import gc
from pathlib import Path

print(os.getcwd())
# print('lala')
sourceDir = '/share/data/cellprofiler/automation/results'
rootDir = '/home/jovyan/scratch2-shared/david/colopaint3D'
OutputDir = 'data/1_FeaturesImages_minmax'
if not os.path.exists(OutputDir): 
    os.makedirs(OutputDir)
NameContains = ''
InputFolders = pl.read_csv('settings/filemap.csv')
print(InputFolders )
now = datetime.datetime.now()
print ('Current date and time : ')
print (now.strftime('%Y-%m-%d %H:%M:%S'))
cols_to_drop = ['index','layout_id','cmpd_code', 'solvent','cmpd_conc','cmpd_conc_unit','stock_conc','stock_conc_unit','cmpd_vol', 'cmpd_vol_unit', 'well_vol', 'well_vol_unit', 'article_id','pubchemID', 'smiles', 'inkey', 'clinical_status']

use_clipping = False

std_mean = True

make_slices = True