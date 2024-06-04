import pandas as pd

df = pd.read_csv('settings/drug-well-map_xls.csv')
df2 = pd.DataFrame(columns=['well-id', 'drug'])
# df3 = pd.DataFrame(columns=['row', 'column', 'drug'])
for rindex, row in df.iterrows():
    # print(row)
    for column, drug in row.items():
        if column != 'row-index':
            print(type(column))
            if len(column) < 2:
                column = '0'+column
            mapdata = [[str(row[0]) + column, drug]]
            # print(mapdata)
            df3 = pd.DataFrame(mapdata, columns=['well-id', 'drug'])
            # print(df3)
            df2 = pd.concat([df2, df3])
        # print(cindex)
df2=df2.reset_index(drop=True)
print(df2)
df2.to_csv('settings/drug-well-map.csv', index=False, sep=',')