import time
import pandas as pd
import logging as log
import object_pickler as op
import global_variables as gv

from sklearn import svm
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import cross_validate
from sklearn.cluster import KMeans, AffinityPropagation, MeanShift

log.basicConfig(filename='document_clustering.log', level=log.DEBUG, filemode="w")


def loadPickle(filename):
    # filename without extension
    return op.load_object(gv.prj_src_path + "python_objects/" + filename)


def cross_validation():
    data_label = [{"data": "train_data_transformed", "label": "train_labels"},
                  {"data": "train_data_hash_transformed", "label": "train_labels"},
                  {"data": "val_data_transformed", "label": "val_labels"},
                  {"data": "val_data_hash_transformed", "label": "val_labels"},
                  {"data": "test_data_transformed", "label": "test_labels"},
                  {"data": "test_data_hash_transformed", "label": "test_labels"}]

    try_algorithms = {"KMeans": KMeans(n_clusters=15), "AffinityPropagation": AffinityPropagation(),
                      "MeanShift": MeanShift(), "SVC": svm.SVC(kernel='linear', C=1, random_state=0),
                      "NB": MultinomialNB(), "LogisticRegression": LogisticRegression(),
                      "SGDClassifier": SGDClassifier()}

    for dl in data_label:
        data = loadPickle(dl["data"])
        labels = loadPickle(dl["label"])
        labels = [gv.translation[x] for x in labels]

        log.info("data: %s" % (dl["data"]))
        for algo, clf in try_algorithms.items():
            scoring = ['precision_macro', 'recall_macro', 'f1_macro', 'accuracy']
            scores = cross_validate(clf, data, labels, scoring=scoring, cv=2,
                                    return_train_score=False)

            for k in sorted(scores.keys()):
                print("\t%s %s %s: %0.2f (+/- %0.2f)" % (dl["data"], algo, k, scores[k].mean(), scores[k].std() * 2))
                log.debug(
                    "\t%s %s %s: %0.2f (+/- %0.2f)" % (dl["data"], algo, k, scores[k].mean(), scores[k].std() * 2))


# def plot_cluster():
#     data = loadPickle("test_data_transformed")
#     labels = loadPickle("test_labels")
#     data_by_labels = dict()
#
#     for index, l in enumerate(labels):
#         data_by_labels[l] = data.get(index)
#
#     data_by_labels = pd.DataFrame.from_dict(data_by_labels)
#
# def cluster():
#     data = loadPickle("train_data_transformed")
#     try_algorithms = {"KMeans": KMeans(n_clusters=15), "AffinityPropagation": AffinityPropagation(),
#                       "MeanShift": MeanShift()}

def run():
    cross_validation()


def main():
    run()


if __name__ == '__main__':
    start_time = time.time()
    log.info(("Document clustering started: ", time.localtime(start_time)))
    main()
    end_time = time.time()
    log.info(("Data processor ended: ", time.localtime(end_time)))
    execution_time = end_time - start_time
    hours, rem = divmod(execution_time, 3600)
    minutes, seconds = divmod(rem, 60)
    log.info(("Data processor executed for {:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)))