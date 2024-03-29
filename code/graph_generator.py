import logging as log
import seaborn as sns
import matplotlib.pyplot as plt


def plot_chart(y, y_label, title, kind, data, pad, plot_name, fig_num):
    plt.figure(fig_num)
    plt.title(title, pad=pad)
    sns_plot = sns.catplot(x="label", y=y, kind=kind, data=data)
    sns_plot.set_xticklabels(rotation=45, ha='right')
    sns_plot.set_axis_labels("Classes", y_label)
    for index, row in data.iterrows():
        sns_plot.ax.text(float(index) - 0.25, row[y], row[y], rotation=45)
    sns_plot.savefig(plot_name + ".png")
    # plt.show()


def plot_cluster(title, data, pad, plot_name, fig_num, l_col, hue):
    palette = ["#273eff", "#f37c04", "#4bc938", "#e82007", "#8b2be2", "#9f4700", "#f24cc1", "#a3a3a3", "#f7c401",
               "#56d8fe", "#cd88a8", "#5ea55a", "#f15357", "#2d70b1", "#000200"]
    classes = data[hue].unique()
    num_classes = classes.shape[0]
    log.debug(title + "num_classes:" + str(num_classes))
    log.debug(title + "classes:")
    log.debug(classes)
    plt.figure(num=fig_num, figsize=(15, 15))
    plt.title(title, pad=pad)
    sns_plot = sns.scatterplot(x="x", y="y", hue=hue, palette=sns.color_palette(palette), data=data,
                               legend="full")
    plt.legend(loc='upper left', bbox_to_anchor=(0.57, 1.13),
               ncol=l_col, fancybox=True, shadow=True)
    sns_plot.figure.savefig(plot_name + ".png")
    # plt.show()
