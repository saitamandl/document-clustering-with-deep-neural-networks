import json
import logging as log
import time

import spacy
from gensim.corpora import Dictionary
from gensim.models import LdaModel
from gensim.models import Phrases
from gensim.models.doc2vec import Doc2Vec
from nltk.stem.wordnet import WordNetLemmatizer
from scipy.sparse import csr as _csr
from sklearn.feature_extraction import DictVectorizer

import file_collector as fc
import global_variables as gv
import object_pickler as op
import timer
from preprocessGenerator import PreprocessGenerator

log.basicConfig(filename='data_processor.log', level=log.DEBUG, filemode="w")


def load_stop_words():
    with open(gv.prj_src_path + "data/stopwords-en.txt", "rt", encoding="utf-8-sig") as infile:
        stopwords_en = json.load(infile)["en"]
        return stopwords_en


def load_lda_dictionary(dict_name):
    return Dictionary.load_from_text("%spython_objects/%s.dict" % (gv.prj_src_path, dict_name))


def preprocess_for_lda(train_corpus_tokens_only):
    lemmatizer = WordNetLemmatizer()
    docs = [[lemmatizer.lemmatize(token) for token in doc] for doc in train_corpus_tokens_only]
    bigram = Phrases(docs, min_count=20)
    for idx in range(len(docs)):
        for token in bigram[docs[idx]]:
            if '_' in token:
                # Token is a bigram, add to document.
                docs[idx].append(token)
    # Create a dictionary representation of the documents.
    dictionary = Dictionary(docs)

    # Filter out words that occur less than 20 documents, or more than 50% of the documents.
    dictionary.filter_extremes(no_below=20, no_above=0.5)
    dictionary.save_as_text("%spython_objects/dataset.dict" % gv.prj_src_path)
    # Bag-of-words representation of the documents.
    corpus = [dictionary.doc2bow(doc) for doc in docs]
    op.save_object(corpus, gv.prj_src_path + "python_objects/corpus")
    log.info("corpus length: %s" % len(corpus))
    return corpus, dictionary


def generate_lda_model(corpus, dictionary, num_topics, passes):
    # Set training parameters.
    chunksize = 2000
    iterations = 400
    eval_every = None  # Don't evaluate model perplexity, takes too much time.

    # Make a index to word dictionary.
    id2word = dictionary.id2token

    lda_model = LdaModel(
        corpus=corpus,
        id2word=id2word,
        chunksize=chunksize,
        alpha='auto',
        eta='auto',
        iterations=iterations,
        num_topics=num_topics,
        passes=passes,
        eval_every=eval_every
    )
    lda_model.save("%spython_objects/document_model_%s_%s.lda" % (gv.prj_src_path, str(num_topics), str(passes)))


def load_doc2vec_model():
    return Doc2Vec.load(gv.prj_src_path + "python_objects/document_model.doc2vec")


def generate_doc2vec_model(train_corpus):
    doc2vec_model = Doc2Vec(vector_size=300, min_count=2, epochs=50)
    doc2vec_model.build_vocab(train_corpus)
    doc2vec_model.train(train_corpus, total_examples=doc2vec_model.corpus_count, epochs=doc2vec_model.iter)
    doc2vec_model.save(gv.prj_src_path + "python_objects/document_model.doc2vec")


def dict_vectorizer(data_dict, label_dict, test_data_dict, test_label_dict, val_data_dict, val_label_dict):
    labels = list()
    test_labels = list()
    val_labels = list()
    data = list()
    test_data = list()
    val_data = list()
    for file_path, value in data_dict.items():
        if len(value) is not 0:
            labels.append(label_dict[file_path])
            data.append(value)

    for file_path, value in test_data_dict.items():
        if len(value) is not 0:
            test_labels.append(test_label_dict[file_path])
            test_data.append(value)

    for file_path, value in val_data_dict.items():
        if len(value) is not 0:
            val_labels.append(val_label_dict[file_path])
            val_data.append(value)

    dv = DictVectorizer(sparse=True)
    data_transformed = dv.fit_transform(data)
    test_data_transformed = dv.transform(test_data)
    val_data_transformed = dv.transform(val_data)
    return data_transformed, labels, test_data_transformed, test_labels, val_data_transformed, val_labels


def tokenizer(required_files):
    stopwords_en = load_stop_words()

    nlp = spacy.load("en_core_web_sm")
    document_meta = dict()
    modified_texts = dict()
    parsed_documents = dict()
    for file_path_ in required_files:
        file_path = gv.data_src_path + file_path_
        lines = fc.read_file(file_path)
        text = "".join(lines)
        parsed_text = nlp(text)
        parsed_documents[file_path_] = parsed_text
        document_meta[file_path_] = dict()
        is_empty = True
        for token in parsed_text:
            if token.pos_ is "NUM":
                token_key = "<NUM>"
                text = text.replace(token.text, token_key).replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ") \
                    .replace("\t", " ")
            else:
                token_key = token.text.strip()
            if len(token_key) > 0 and token_key not in stopwords_en:
                document_meta[file_path_][token_key] = 1.0
                is_empty = False
        if not is_empty:
            modified_texts[file_path_] = text
    return document_meta, modified_texts


def run():
    # # train labels
    # label_start = time.time()
    # log.info(("Get train labels: ", time.localtime(label_start)))
    # train_paths_by_label, train_labels_by_path = dl.get_labels(
    #     fc.read_file(gv.data_src_path + gv.train_label_file_name), gv.train_label_file_name)
    # log.debug("train_paths_by_label: " + str(len(train_paths_by_label)))
    # log.debug("train_labels_by_path: " + str(len(train_labels_by_path)))
    # timer.time_executed(label_start, "Get train labels")
    # # test labels
    # label_start = time.time()
    # log.info(("Get test labels: ", time.localtime(label_start)))
    # test_paths_by_label, test_labels_by_path = dl.get_labels(fc.read_file(gv.data_src_path + gv.test_label_file_name),
    #                                                          gv.test_label_file_name)
    # log.debug("test_paths_by_label: " + str(len(test_paths_by_label)))
    # log.debug("test_labels_by_path: " + str(len(test_labels_by_path)))
    # timer.time_executed(label_start, "Get test labels")
    #
    # # val labels
    # label_start = time.time()
    # log.info(("Get val labels: ", time.localtime(label_start)))
    # val_paths_by_label, val_labels_by_path = dl.get_labels(fc.read_file(gv.data_src_path + gv.val_label_file_name),
    #                                                        gv.val_label_file_name)
    # log.debug("val_paths_by_label: " + str(len(val_paths_by_label)))
    # log.debug("val_labels_by_path: " + str(len(val_labels_by_path)))
    # timer.time_executed(label_start, "Get val labels")
    #
    # # train dataset processing
    # process_start = time.time()
    # log.info(("Process train data: ", time.localtime(process_start)))
    # train_document_meta, train_modified_texts = tokenizer(required_files=train_labels_by_path)
    # log.debug("train_document_meta: " + str(len(train_document_meta)))
    # log.debug("train_modified_texts: " + str(len(train_modified_texts)))
    # timer.time_executed(process_start, "Process train data")
    # op.save_object(train_document_meta, gv.prj_src_path + "python_objects/train_document_meta")
    # op.save_object(train_modified_texts, gv.prj_src_path + "python_objects/train_modified_texts")
    #
    # # test dataset processing
    # process_start = time.time()
    # log.info(("Process test data: ", time.localtime(process_start)))
    # test_document_meta, test_modified_texts = tokenizer(required_files=test_labels_by_path)
    # log.debug("test_document_meta: " + str(len(test_document_meta)))
    # log.debug("test_modified_texts: " + str(len(test_modified_texts)))
    # timer.time_executed(process_start, "Process test data")
    # op.save_object(test_document_meta, gv.prj_src_path + "python_objects/test_document_meta")
    # op.save_object(test_modified_texts, gv.prj_src_path + "python_objects/test_modified_texts")
    #
    # # val dataset processing
    # process_start = time.time()
    # log.info(("Process val data: ", time.localtime(process_start)))
    # val_document_meta, val_modified_texts = tokenizer(required_files=val_labels_by_path)
    # log.debug("val_document_meta: " + str(len(val_document_meta)))
    # log.debug("val_modified_texts: " + str(len(val_modified_texts)))
    # timer.time_executed(process_start, "Process val data")
    # op.save_object(val_document_meta, gv.prj_src_path + "python_objects/val_document_meta")
    # op.save_object(val_modified_texts, gv.prj_src_path + "python_objects/val_modified_texts")
    #
    # # stopwords_en = load_stop_words()
    #
    # # load document meta
    # train_document_meta = op.load_object(gv.prj_src_path + "python_objects/train_document_meta")
    # test_document_meta = op.load_object(gv.prj_src_path + "python_objects/test_document_meta")
    # val_document_meta = op.load_object(gv.prj_src_path + "python_objects/val_document_meta")
    #
    # # dict_vectorizer
    # process_start = time.time()
    # log.info(("Dictvectorizer: ", time.localtime(process_start)))
    # train_data_transformed, train_labels, test_data_transformed, test_labels, val_data_transformed, val_labels = \
    #     dict_vectorizer(data_dict=train_document_meta, label_dict=train_labels_by_path,
    #                     test_data_dict=test_document_meta, test_label_dict=test_labels_by_path,
    #                     val_data_dict=val_document_meta, val_label_dict=val_labels_by_path)
    # log.debug("train_labels: " + str(len(train_labels)))
    # log.debug("test_labels: " + str(len(test_labels)))
    # log.debug("val_labels: " + str(len(val_labels)))
    # timer.time_executed(process_start, "Dictvectorizer")
    #
    # op.save_object(train_data_transformed, gv.prj_src_path + "python_objects/train_data_transformed")
    # op.save_object(train_labels, gv.prj_src_path + "python_objects/train_labels")
    #
    # op.save_object(test_data_transformed, gv.prj_src_path + "python_objects/test_data_transformed")
    # op.save_object(test_labels, gv.prj_src_path + "python_objects/test_labels")
    #
    # op.save_object(val_data_transformed, gv.prj_src_path + "python_objects/val_data_transformed")
    # op.save_object(val_labels, gv.prj_src_path + "python_objects/val_labels")
    #
    # # load modified texts
    train_modified_texts = op.load_object(gv.prj_src_path + "python_objects/train_modified_texts")
    # test_modified_texts = op.load_object(gv.prj_src_path + "python_objects/test_modified_texts")
    # val_modified_texts = op.load_object(gv.prj_src_path + "python_objects/val_modified_texts")
    #
    # # generate preprocessed train corpus
    process_start = time.time()
    log.info(("Train corpus: ", time.localtime(process_start)))
    train_corpus_list = [tcd for key, tcd in train_modified_texts.items()]
    # train_corpus_preprocessed = PreprocessGenerator(train_corpus_list)
    log.info("train_corpus size: " + str(len(train_corpus_list)))
    timer.time_executed(process_start, "Train corpus")

    # generate tokens only train corpus
    process_start = time.time()
    log.info(("Train corpus: ", time.localtime(process_start)))
    train_corpus_tokens_only = PreprocessGenerator(train_corpus_list, tokens_only=True)
    timer.time_executed(process_start, "Train corpus")

    # # generate tokens only Test corpus
    # process_start = time.time()
    # log.info(("Test corpus: ", time.localtime(process_start)))
    # test_corpus_list = [tcd for key, tcd in test_modified_texts.items()]
    # test_corpus_tokens_only = PreprocessGenerator(test_corpus_list, tokens_only=True)
    # log.info("test_corpus size: " + str(len(test_corpus_list)))
    # timer.time_executed(process_start, "Test corpus")
    #
    # # generate tokens only val corpus
    # process_start = time.time()
    # log.info(("Val corpus: ", time.localtime(process_start)))
    # val_corpus_list = [tcd for key, tcd in val_modified_texts.items()]
    # val_corpus_tokens_only = PreprocessGenerator(val_corpus_list, tokens_only=True)
    # log.info("val_corpus size: " + str(len(val_corpus_list)))
    # timer.time_executed(process_start, "Val corpus")
    #
    # # generate doc2vec model
    # process_start = time.time()
    # log.info(("Doc2Vec: ", time.localtime(process_start)))
    # generate_doc2vec_model(train_corpus_preprocessed)
    # timer.time_executed(process_start, "Doc2Vec")
    #
    # # load doc2vec model
    # model = load_doc2vec_model()
    #
    # # get train vector from the doc2vec
    # infer_vector_start = time.time()
    # log.info(("Infer vector train: ", time.localtime(process_start)))
    # train_vector = list(map(model.infer_vector, train_corpus_tokens_only))
    # log.info("train_vector size: " + str(len(train_vector)))
    # rand_index = randrange(len(train_vector))
    # log.info("train_vector[" + str(rand_index) + "] feature size: " + str(len(train_vector[rand_index - 1])))
    # log.info(train_vector[rand_index])
    # timer.time_executed(infer_vector_start, "Infer vector train")
    # op.save_object(train_vector, gv.prj_src_path + "python_objects/train_vector")
    #
    # # get test vector from the doc2vec
    # infer_vector_start = time.time()
    # log.info(("Infer vector test: ", time.localtime(process_start)))
    # test_vector = list(map(model.infer_vector, test_corpus_tokens_only))
    # log.info("test_vector size: " + str(len(test_vector)))
    # rand_index = randrange(len(test_vector))
    # log.info("test_vector[" + str(rand_index) + "] feature size: " + str(len(test_vector[rand_index - 1])))
    # log.info(test_vector[rand_index])
    # timer.time_executed(infer_vector_start, "Infer vector test")
    # op.save_object(test_vector, gv.prj_src_path + "python_objects/test_vector")
    #
    # # get val vector from the doc2vec
    # infer_vector_start = time.time()
    # log.info(("Infer vector val: ", time.localtime(process_start)))
    # val_vector = list(map(model.infer_vector, val_corpus_tokens_only))
    # log.info("val_vector size: " + str(len(val_vector)))
    # rand_index = randrange(len(val_vector))
    # log.info("val_vector[" + str(rand_index) + "] feature size: " + str(len(val_vector[rand_index - 1])))
    # log.info(val_vector[rand_index])
    # timer.time_executed(infer_vector_start, "Infer vector val")
    # op.save_object(val_vector, gv.prj_src_path + "python_objects/val_vector")

    # preprocess for lda
    process_start = time.time()
    log.info(("Preprocess LDA: ", time.localtime(process_start)))
    corpus, dictionary = preprocess_for_lda(train_corpus_tokens_only)
    timer.time_executed(process_start, "Preprocess LDA")

    dictionary = load_lda_dictionary("dataset")
    corpus = op.load_object(gv.prj_src_path + "python_objects/corpus")
    # generate lda models
    process_start = time.time()
    log.info(("LDA_20_20: ", time.localtime(process_start)))
    generate_lda_model(corpus, dictionary, num_topics=20, passes=20)
    timer.time_executed(process_start, "LDA_20_20")

    process_start = time.time()
    log.info(("LDA_50_10: ", time.localtime(process_start)))
    generate_lda_model(corpus, dictionary, num_topics=50, passes=10)
    timer.time_executed(process_start, "LDA_50_10")

    process_start = time.time()
    log.info(("LDA_30_20: ", time.localtime(process_start)))
    generate_lda_model(corpus, dictionary, num_topics=30, passes=20)
    timer.time_executed(process_start, "LDA_30_20")


def main():
    run()


if __name__ == '__main__':
    start_time = time.time()
    log.info(("Data processor started: ", time.localtime(start_time)))
    try:
        main()
    except Exception as ex:
        log.exception(ex)
    timer.time_executed(start_time, "Data processor")
