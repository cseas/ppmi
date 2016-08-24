from collections import namedtuple

import numpy as np
import ppmilib.utils as utils
from ppmilib.patient import Patient, PatientDict
from ppmilib.datadictionary import DataDictionary
import corex.corex as ce

from ete3 import Tree, ClusterTree, TreeStyle

# Get the UPDRS Part 3 data
mds_updrs_3 = utils.fetch_ppmi_data_file("MDS_UPDRS_Part_III__Post_Dose_.csv", 
                                         "motor")
# Create a mask of the baseline
baseline_mask = (mds_updrs_3.EVENT_ID == "BL")
# Create a mask of the NUPDRS3 page (this is pre-dose)
pagename_mask = (mds_updrs_3.PAG_NAME == "NUPDRS3")

# dataframe of baseline UPDRS3 data
mds_updrs_3_bl = mds_updrs_3[baseline_mask & pagename_mask]

# Extract the column names for the subscores of UPDRS3
updrs3_column_names = [x for x in mds_updrs_3_bl.columns if 
        (x[:2] == "NP" or x[:2] == "PN")]
# There should be 33 variables
len(updrs3_column_names) == 33

# Create a dictionary that expands the column names into descriptions
data_dict = DataDictionary.create()
column_namesd = data_dict.get_column_dict("NUPDRS3")

# Create a Patients Dictionary
patient_dict = PatientDict.create()

# Create masks of enrolled patients and PD patients
enrolled_mask = patient_dict.get_enrolled_mask(mds_updrs_3_bl.PATNO)
pd_mask = patient_dict.get_pd_mask(mds_updrs_3_bl.PATNO)

# Reduce to only enrolled PD patients
mds_updrs_3_bl_enrolled_pd = mds_updrs_3_bl[enrolled_mask & pd_mask]

def PrepareForCorex(df, updrs3_column_names):
    """Prepare the dataframe for input into Corex"""
    # reduce to part 3 variables only
    x = df[updrs3_column_names]
    # drop NA's for now. FIXME: replace by -1's later
    x = x.dropna()
    # cast to integer matrix
    x = x.as_matrix().astype(np.int_)
    return x

mds_updrs_3_bl_values = PrepareForCorex(mds_updrs_3_bl, updrs3_column_names)
print(mds_updrs_3_bl_values.shape)

mds_updrs_3_bl_enrolled_pd_values = PrepareForCorex(mds_updrs_3_bl_enrolled_pd, 
        updrs3_column_names)
print(mds_updrs_3_bl_enrolled_pd_values.shape)

updrs3_expanded_column_names = [column_namesd[x] for x in updrs3_column_names]

def CreateListOfClusters(layer, prev_clusters):
    """ Take a list of clusters and cluster them further based on layer"""
    assert(layer.clusters.size == len(prev_clusters))
    retl =  [list() for _ in range(0, layer.n_hidden)]
    Node = namedtuple('Node', ['distance', 'child'])
    for i, idx in enumerate(layer.clusters):
        n = Node(distance=layer.tcs[idx], child=prev_clusters[i])
        retl[idx].append(n)
    return retl

X = mds_updrs_3_bl_values
#X = mds_updrs_3_bl_enrolled_pd_values

layer1 = ce.Corex(n_hidden=12, dim_hidden=5)
Y1 = layer1.fit_transform(X)
layer1.clusters
C1 = np.unique(layer1.clusters).size
layer1.tc # 5.09
layer1.tcs
Y1.shape
layer1.labels[0]
retl = CreateListOfClusters(layer1, updrs3_expanded_column_names)
retl


#layer2 = ce.Corex(n_hidden=C1-1)
layer2 = ce.Corex(n_hidden=5, dim_hidden=5)
Y2 = layer2.fit_transform(Y1)
layer2.clusters
C2 = np.unique(layer1.clusters).size
layer2.tc
layer2.tcs

retl2 = CreateListOfClusters(layer2, retl)
retl2

def ConvertListofClustersToTree(cluster_list):
    """ FIXME: recurse this function"""
    t = Tree()
    for i, node in enumerate(cluster_list):
        print "Cluster %d"%i
        if (len(node)) >= 1:
            print "We have a node of size : %d" % len(node)
            child = t.add_child(name="Cluster %d"%i)
            for subnode in node:
                if len(subnode.child) >= 1:
                    print "Adding subnode of size : %d"%len(subnode.child)
                    for subsubnode in subnode.child:
                        print "Adding subsubnode of %s"%subsubnode.child
                        child.add_child(name=subsubnode.child, dist=subsubnode.distance)
    return t

t = ConvertListofClustersToTree(retl2)
t.show()
#ts = TreeStyle()
#ts.mode = 'c'
#t.show(tree_style=ts)



