import io
import re
import itertools
from os.path import join
from collections import Counter
import numpy as np


def clean_str(string):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()


def _balance(p, n):
    num_pos = len(p)
    num_neg = len(n)
    new_num = min(num_pos, num_neg)
    if (num_pos == num_neg):
        print "training set is already balanced"
    elif (num_neg > new_num):
        n = np.random.choice(n, size=new_num, replace=False)
        print "balanced training set by reducing negtive to {0}".format(new_num)
    else:
        p = np.random.choice(p, size=new_num, replace=False)
        print "balanced training set by reducing positive to {0}".format(new_num)
    return (p, n)


def load_data_and_labels(positive_data_file, negative_data_file):
    """
    Loads MR polarity data from files, splits the data into words and generates labels.
    Returns split sentences and labels.
    """
    # Load data from files
    positive_examples = list(open(positive_data_file, "r").readlines())
    positive_examples = [s.strip() for s in positive_examples]
    negative_examples = list(open(negative_data_file, "r").readlines())
    negative_examples = [s.strip() for s in negative_examples]
    # balance positive and negative examples
    positive_examples, negative_examples = _balance(positive_examples, negative_examples)
    # Split by words
    x_text = positive_examples + negative_examples
    x_text = [clean_str(sent) for sent in x_text]
    # Generate labels
    positive_labels = [[0, 1] for _ in positive_examples]
    negative_labels = [[1, 0] for _ in negative_examples]
    y = np.concatenate([positive_labels, negative_labels], 0)
    return [x_text, y]


def load_data_and_labels_v2(x_path, y_path):
    x_text = list(io.open(x_path, 'r', encoding='utf-8').readlines())
    y = list(io.open(y_path, 'r', encoding='utf-8').readlines())

    x_text = [s.strip() for s in x_text]
    y = np.array([int(s.strip()) for s in y])
    assert len(x_text) == len(y)

    # one-hot encode the integer labels in y
    n = len(y)
    n_labels = len(np.unique(y))
    y_enc = np.zeros((n, n_labels), dtype=np.int32)
    y_enc[np.arange(n), y] = 1
    assert len(x_text) == len(y_enc)
    return [x_text, y_enc]

def load_data_and_labels_twoclass(x_path, y_path):
    x_text = list(io.open(x_path, 'r', encoding='utf-8').readlines())
    y = list(io.open(y_path, 'r', encoding='utf-8').readlines())

    x_text = [s.strip() for s in x_text]
    y = np.array([int(s.strip()) for s in y])
    assert len(x_text) == len(y)

    # balance
    df = pd.DataFrame({'text': x_text, 'y': y})
    num_neg = (df.y == 0).sum()
    num_pos = (df.y == 1).sum()
    positive_examples = df.loc[df.y==1].text
    negative_examples = df.loc[df.y==0].text

    positive_examples, negative_examples = _balance(positive_examples, negative_examples)
    # balance returns changed things as ndarray
    x_all = pd.Series(positive_examples).append(pd.Series(negative_examples))
    positive_labels = [[0, 1] for _ in positive_examples]
    negative_labels = [[1, 0] for _ in negative_examples]
    y_enc = np.concatenate([positive_labels, negative_labels], 0)
    return [x_all, y_enc]


def load_data_and_labels_v3(base_dir):
    "Combine french and english language files."

    print('\nCombining language files...\n')

    x_path = join(base_dir, 'x-en.txt')
    y_path = join(base_dir, 'y-en.txt')

    x_text = list(io.open(x_path, 'r', encoding='utf-8').readlines())
    y = list(io.open(y_path, 'r', encoding='utf-8').readlines())

    assert len(x_text) == len(y)
    print('n_en = {:,}'.format(len(y)))

    x_path = join(base_dir, 'x-fr.txt')
    y_path = join(base_dir, 'y-fr.txt')

    x_text_fr = list(io.open(x_path, 'r', encoding='utf-8').readlines())
    y_fr = list(io.open(y_path, 'r', encoding='utf-8').readlines())

    assert len(x_text_fr) == len(y_fr)
    print('n_fr = {:,}'.format(len(y_fr)))

    x_text += x_text_fr
    y += y_fr

    print('n_both = {:,}'.format(len(y)))

    x_text = [s.strip() for s in x_text]
    y = np.array([int(s.strip()) for s in y])
    assert len(x_text) == len(y)

    # one-hot encode the integer labels in y
    n = len(y)
    n_labels = len(np.unique(y))
    y_enc = np.zeros((n, n_labels), dtype=np.int32)
    y_enc[np.arange(n), y] = 1
    assert len(x_text) == len(y_enc)
    return [x_text, y_enc]


def batch_iter(data, batch_size, num_epochs, shuffle=True):
    """
    Generates a batch iterator for a dataset.
    """
    data = np.array(data)
    data_size = len(data)
    num_batches_per_epoch = int((len(data)-1)/batch_size) + 1
    for epoch in range(num_epochs):
        # Shuffle the data at each epoch
        if shuffle:
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data = data[shuffle_indices]
        else:
            shuffled_data = data
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, data_size)
            yield shuffled_data[start_index:end_index]
