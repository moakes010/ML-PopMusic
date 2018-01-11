import requests
import pandas as pd
from lxml import html
import sys

#bb2016_url='http://www.billboard.com/charts/year-end/2016/hot-100-songs'
URL='http://www.billboard.com'

def _url(chart, year):
    return "/".join((URL, 'charts/year-end', year, chart))
    

def GetTop100(url, year):
    '''
    Scrap Billboard charts year-end url for top 100 artists and songs
    and return a pandas DataFrame
    '''
    r = requests.get(url)
    if r.status_code == 200:
        root = html.fromstring(r.content)
        rank = root.xpath('//div[@class="ye-chart__item-rank"]/text()')
        artist = root.xpath('//h2[@class="ye-chart__item-subtitle"]//a[@class="ye-chart__item-subtitle-link"]/text()')
        song = root.xpath('//h1[@class="ye-chart__item-title"]/text()')
        artists = [ a.replace('\n','') for a in artist ]
        songs = [ s.replace('\n','') for s in song ]

        bb_list = [('Rank', rank), 
        ('Song', songs),
        ('Artist', artists),
        ('Year', year)
        ]
        df = pd.DataFrame.from_items(bb_list)
    else:
        print(r.status_code)
        sys.exit(1)
    return df

if __name__ == "__main__":
    if len(sys.argv) == 4:
        chart = sys.argv[1]
        year = sys.argv[2]
        csv_path = sys.argv[3]
        #TODO Probaby should do input validation
        bburl = _url(chart, year)
        bb_df = GetTop100(bburl, year)
        bb_df.to_csv(csv_path)
    else:
        print("Usage: python BillboardTop100Scrap.py <url> <csv_path>")
