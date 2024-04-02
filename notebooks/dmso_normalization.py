import os
import pandas as pd
import numpy as np
import cv2
import albumentations as album
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(filename='logfile.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def main():
    # Set current working directory
    current_directory = "/share/data/analyses/ahmet/rms_specs_deep"
    os.chdir(current_directory)
    logging.info(f"Current working directory: {os.getcwd()}")

    # Load the image metadata
    df = pd.read_csv('images_metadata_channels.csv', delimiter=';')
    df = df.sample(frac=1, random_state=1)  # Shuffle the data

    # Save the shuffled DataFrame to a CSV file
    shuffled_csv_path = 'shuffled_images_metadata_channels.csv'
    df.to_csv(shuffled_csv_path, sep=';', index=False)

    # Load DMSO statistics
    dmso_stats_df = pd.read_csv('rh30_dmso_channel_stats_final.csv', delimiter=';', header=[0,1], index_col=0)

    # Processing and saving images
    all_images = process_and_save_images(df, dmso_stats_df)

    # Save the processed images
    with open('all_images.npy', 'wb') as f:
        np.save(f, all_images)

def dmso_normalization(im, dmso_mean, dmso_mad):
    return (im.astype('float') - dmso_mean) / dmso_mad

def process_and_save_images(df, dmso_stats_df):
    image_size = 256
    easy_transforms = album.Compose([album.Resize(image_size, image_size)])
    all_images = np.zeros((df.shape[0], image_size, image_size, 5), dtype = np.float32)

    for f in tqdm(range(df.shape[0]), desc='Processing Images'):
        all_images[f] = create_all_images(f, df, dmso_stats_df, easy_transforms)
        logging.info(f"Processed image {f+1}/{df.shape[0]}")
    
    return all_images

def create_all_images(idx, df, dmso_stats_df, easy_transforms):
    row = df.iloc[idx]
    im = []
    for i in range(1,6):
        local_im = cv2.imread(row['w' + str(i)], -1)
        dmso_mean = dmso_stats_df[row.Metadata_Barcode]['w' + str(i)]['Median']
        dmso_mad = dmso_stats_df[row.Metadata_Barcode]['w' + str(i)]['MAD']
        local_im = dmso_normalization(local_im, dmso_mean, dmso_mad)
        im.append(local_im)
    im = np.array(im).transpose(1, 2, 0).astype("float")
    im = np.array(easy_transforms(image = im)['image'])
    return im

if __name__ == "__main__":
    main()

