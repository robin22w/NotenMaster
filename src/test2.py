import numpy as np
import pandas as pd

num_pdf_pages=5

# Create arrays
array1 = np.arange(1, num_pdf_pages + 1)
array2 = np.zeros((4, num_pdf_pages))

# Reshape array1 to have the same number of dimensions as array2
array1_reshaped = array1.reshape(1, -1)

# Stack the arrays along a new axis
#result = np.stack((array1_reshaped, array2), axis=0)

#print(np.concatenate((array1_reshaped, array2)))

df = pd.DataFrame(
    np.stack((
        np.arange(1,num_pdf_pages+1),
        np.zeros((num_pdf_pages))),
        axis=1),
    columns=["page", "instrument"]
    )


df = df.join(pd.DataFrame(
    {
        'column_new_1': None,
        'column_new_2': None,
        'column_new_3': None
    }, index=df.index
))
print(df)


df.loc[df.index[df['page']==2]] = 2,4,3,3,3
print(df)
