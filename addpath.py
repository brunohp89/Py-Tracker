import sys
import os

wdir = os.getcwd() + "\\system"
if wdir not in sys.path:
    sys.path.insert(0, wdir)

# ------------------------------------------------------------------------------------------------------#
# Added class remapping to avoid/solve pickle-pandas incompatibility in different versions combinations #
# see question StockOverflow 54665527                                                                   #
# ------------------------------------------------------------------------------------------------------#
from pandas.compat.pickle_compat import _class_locations_map

_class_locations_map.update({
    ('pandas.core.internals.managers', 'BlockManager'): ('pandas.core.internals', 'BlockManager')
})
# ------------------------------------------------------------------------------------------------------#
