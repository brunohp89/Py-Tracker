import pandas as pd
import tracker_library as tl


def get_csv_from_google_drive(urldrive):
    url = urldrive
    path = 'https://drive.google.com/uc?export=download&id=' + url.split('/')[-2]
    df = pd.read_csv(path)
    return df


def remove_date_from_dict(hist_dict, dates=None):
    if dates is None:
        return "At least one datetime contained in the hist_dict keys has to be passed"
    for dat in dates:
        keys = list(hist_dict.keys())
        for k in keys:
            hist_dict[k].pop(dat)


def separate_custodial(pByExchange):
    other = tl.other_tokens()
    if other is not None:
        other.drop('Amount', axis=1, inplace=True)
        other.reset_index(inplace=True, drop=True)
        for set1 in tl.setup:
            other = other.append(pd.DataFrame({'Location': [set1.get('name')],
                                               'IsCustodial': [set1.get('isCustodial')]}))
    else:
        other = pd.DataFrame({'Location': [], 'IsCustodial': []})
        for set1 in tl.setup:
            other = other.append(pd.DataFrame({'Location': [set1.get('name')],
                                               'IsCustodial': [set1.get('isCustodial')]}))

    other.index = other['Location'].tolist()
    other.drop("Location", axis=1, inplace=True)
    vout = pd.merge(other, pByExchange, left_index=True, right_index=True).groupby(['IsCustodial']).sum()
    vout = pd.Series(vout[0])
    return vout


def check_drive_folder(namef, drive, loc='root'):
    # Check if application folder exits
    drivelist = drive.ListFile({'q': f"'{loc}' in parents and trashed=false"}).GetList()
    drivelist = [f.metadata.get('id') for f in drivelist if f.metadata.get('title') == namef]

    if len(drivelist) == 0:
        # Create a new folder
        folder_name = namef
        foldernew = drive.CreateFile({'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder',
                                      'parents': [dict({'id': loc})]})
        foldernew.Upload()

    drivelist = drive.ListFile({'q': f"'{loc}' in parents and trashed=false"}).GetList()
    drivelist = [f.metadata.get('id') for f in drivelist if f.metadata.get('title') == namef]

    return drivelist[0]
