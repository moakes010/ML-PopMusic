# Overview 

The following work looks to explore and examine music popularity in the United States 
by applying data science tools and principles.  Billboard releases the Top 100 at the end
of the year since 1958.  Can one build a model to predict which songs will end show up in 
the top 100 for a given year? 

A great deal of effort was placed into generating the dataset (10192 observations), collecting 
audio features from the Spotify Web API.  

Spotify Web API: https://developer.spotify.com/web-api/

# Motivation 

From 1999-2016, the global recorded music industry contracted from 22.8
to 15.7 billion with 100% of revenue generated from physical records in 1999
to only 34% in 2016. A catalyst for the diversification of the industry was
most likely impacted by the release of the P2P music file sharing service, Napster
in 1999 which revolutionized how an individual user can discover and share music.
The music industry reluctance to embrace emerging technology caused a contraction 
in market share but on-demand streaming services are revitalizing the industry.  On-demand 
streaming services, like Spotify, generate a trove of data. 

#  Contents

-analysis folder contains jupyter notebook to examine data
-collection folder contains billboard web scrap and audio feature collection tools interacting with the
Spotify API
-data folder includes datasets from the LabROSA million song dataset and billboard lists. 
