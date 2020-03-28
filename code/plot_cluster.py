import time
import timer
import pandas as pd
import logging as log
import object_pickler as op
import global_variables as gv
import graph_generator as gg

from sklearn.manifold import TSNE

log.basicConfig(filename='plot_cluster.log', level=log.DEBUG, filemode="w")


def loadPickle(filename):
    # filename without extension
    return op.load_object(gv.prj_src_path + "python_objects/" + filename)


def run():
    predicted_label = {"unsupervised": ["KMeans_"],
                       "supervised": ["LogisticRegression_", "NB_", "SVC_"]}
    target_names = [gv.label_name[i] for i in gv.translation_rev]

    # test_transformed = loadPickle("test_data_transformed")
    # test_embedded = TSNE(n_components=2).fit_transform(test_transformed)
    # op.save_object(test_embedded, gv.prj_src_path + "python_objects/test_2d_data_transformed")
    test_embedded = loadPickle("test_2d_data_transformed")

    df = pd.DataFrame(test_embedded, columns=["x", "y"])
    for algo in predicted_label["supervised"]:
        predict = loadPickle(algo + "test_data_transformed_predict")
        df["label"] = [target_names[p] for p in predict]
        gg.plot_cluster(title=algo, data=df, pad=5, plot_name=gv.prj_src_path + "generated_plots/" + algo, fig_num=1)

    for algo in predicted_label["unsupervised"]:
        predict = loadPickle(algo + "test_data_transformed_predict")
        df["label"] = predict
        gg.plot_cluster(title=algo, data=df, pad=5, plot_name=gv.prj_src_path + "generated_plots/" + algo, fig_num=1)

    labels = loadPickle("test_labels")
    labels = [gv.translation[x] for x in labels]
    df["label"] = labels
    gg.plot_cluster(title="Ground truth", data=df, pad=5, plot_name=gv.prj_src_path + "generated_plots/ground_truth",
                    fig_num=1)


def main():
    run()


if __name__ == '__main__':
    start = time.time()
    log.info(("PLot cluster started: ", time.localtime(start)))
    try:
        main()
    except Exception as ex:
        log.error(ex)
    timer.time_executed(start, "Plot cluster")
