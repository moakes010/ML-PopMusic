#Million Song Dataset Features
import sys
import os
import time
import tables
from collections import OrderedDict
import pandas as pd
import numpy as np

def DataFrameGeneration(FilePath):
    file_count=0
    observations=[]
    for i,(curdir,dirs,files) in enumerate(os.walk(FilePath)):
        print(i)
        file_count += len(files)
        for target in files:
            #h5 = hdf5.open_h5_file_read(os.path.join(curdir,target))
            h5 = tables.open_file(os.path.join(curdir,target), mode='r')
            #num = hdf5.get_num_songs(h5)
            num = h5.root.metadata.songs.nrows
            for song in range(0, num):
                #Artist = hdf5.get_artist_name(h5,songidx=song)
                Artist = h5.root.metadata.songs.cols.artist_name[song]
                #Title = hdf5.get_title(h5,songidx=song)
                Title = h5.root.metadata.songs.cols.title[song]
                if Title == "":
                    
                Year = h5.root.musicbrainz.songs.cols.year[song]

                #Year = hdf5.get_year(h5,songidx=song)
                #Dance = hdf5.get_danceability(h5,songidx=song)
                #Duration = hdf5.get_duration(h5,songidx=song)
                #Energy = hdf5.get_energy(h5,songidx=song)
                #Key = hdf5.get_key(h5,songidx=song)
                #Loud = hdf5.get_loudness(h5,songidx=song)
                #Mode = hdf5.get_mode(h5,songidx=song)
                #Tempo = hdf5.get_tempo(h5,songidx=song)
                #TS = hdf5.get_time_signature(h5,songidx=song)
                #Hotness = hdf5.get_song_hotttnesss(h5,songidx=song)
                observations.append(OrderedDict({'Artist' : Artist, 'Song' : Title, 'Year' : Year})) 
                #'Year' : Year,
                #'Danceability' : Dance, 'Duration' : Duration, 'Energy' : Energy, 'Key' : Key, 
                #'Loud' : Loud, 'Mode' : Mode, 'Tempo' : Tempo, 'Time Signature' : TS, 'Popularity' : Hotness}))

            h5.close()
            obs = pd.DataFrame(observations)
    return obs

if __name__ == "__main__":
    if len(sys.argv) == 3:
        if os.path.exists(sys.argv[1]):
            msd_path = sys.argv[1]
        else:
            print("Path does not exist")
            sys.exit(1)
        csv_path = sys.argv[2]
        #TODO Probaby should do input validation
        msd_df = DataFrameGeneration(msd_path)
        msd_df.to_csv(csv_path)
    else:
        print("Usage: python GetArtistTrackListing.py <path_to_data> <csv_path>")