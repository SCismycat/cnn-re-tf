# -*- coding: utf-8 -*-

import sys
import os
import re
from codecs import open as codecs_open
import cPickle as pickle
import numpy as np



# Special vocabulary symbols.
PAD_TOKEN = '<pad>' # pad symbol
UNK_TOKEN = '<unk>' # unknown word
BOS_TOKEN = '<bos>' # begin-of-sentence symbol
EOS_TOKEN = '<eos>' # end-of-sentence
NUM_TOKEN = '<num>' # numbers

# we always put them at the start.
_START_VOCAB = [PAD_TOKEN, UNK_TOKEN]
PAD_ID = 0
UNK_ID = 1

# Regular expressions used to tokenize.
_DIGIT_RE = re.compile(br"^\d+$")


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
RANDOM_SEED = 1234

def basic_tokenizer(sequence, bos=True, eos=True):
    sequence = re.sub(r'\s{2}', ' ' + EOS_TOKEN + ' ' + BOS_TOKEN + ' ', sequence)
    if bos:
        sequence = BOS_TOKEN + ' ' + sequence.strip()
    if eos:
        sequence = sequence.strip() + ' ' + EOS_TOKEN
    return sequence.lower().split()


def create_vocabulary(vocabulary_path, data_path, max_vocabulary_size, tokenizer=None, bos=True, eos=True):
    """Create vocabulary file (if it does not exist yet) from data file.

    Original taken from
    https://github.com/tensorflow/tensorflow/blob/master/tensorflow/models/rnn/translate/data_utils.py
    """
    if not os.path.exists(vocabulary_path):
        print("Creating vocabulary %s from data %s" % (vocabulary_path, data_path))
        vocab = {}
        with codecs_open(data_path, "rb", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.split('\t')
                if len(line) > 1:
                    line = line[1].strip()
                else:
                    line = line[0].strip()
                tokens = tokenizer(line) if tokenizer else basic_tokenizer(line, bos, eos)
                for w in tokens:
                    word = re.sub(_DIGIT_RE, NUM_TOKEN, w)
                    if word in vocab:
                        vocab[word] += 1
                    else:
                        vocab[word] = 1
            vocab_list = _START_VOCAB + sorted(vocab, key=vocab.get, reverse=True)
            if len(vocab_list) > max_vocabulary_size:
                print("  %d words found. Truncate to %d." % (len(vocab_list), max_vocabulary_size))
                vocab_list = vocab_list[:max_vocabulary_size]
            with codecs_open(vocabulary_path, "wb", encoding="utf-8") as vocab_file:
                for w in vocab_list:
                    vocab_file.write(w + b"\n")



def initialize_vocabulary(vocabulary_path):
    """Initialize vocabulary from file.

    Original taken from
    https://github.com/tensorflow/tensorflow/blob/master/tensorflow/models/rnn/translate/data_utils.py
    """
    if os.path.exists(vocabulary_path):
        rev_vocab = []
        with codecs_open(vocabulary_path, "rb", encoding="utf-8") as f:
            rev_vocab.extend(f.readlines())
        rev_vocab = [line.strip() for line in rev_vocab]
        vocab = dict([(x, y) for (y, x) in enumerate(rev_vocab)])
        return vocab, rev_vocab
    else:
        raise ValueError("Vocabulary file %s not found.", vocabulary_path)


def sentence_to_token_ids(sentence, vocabulary, tokenizer=None, bos=True, eos=True):
    """Convert a string to list of integers representing token-ids.

    Original taken from
    https://github.com/tensorflow/tensorflow/blob/master/tensorflow/models/rnn/translate/data_utils.py
    """
    words = tokenizer(sentence) if tokenizer else basic_tokenizer(sentence, bos, eos)
    return [vocabulary.get(re.sub(_DIGIT_RE, NUM_TOKEN, w), UNK_ID) for w in words]


def data_to_token_ids(data_path, target_path, vocabulary_path, tokenizer=None, bos=True, eos=True):
    """Tokenize data file and turn into token-ids using given vocabulary file.

    Original taken from
    https://github.com/tensorflow/tensorflow/blob/master/tensorflow/models/rnn/translate/data_utils.py
    """
    if not os.path.exists(target_path):
        print("Vectorizing data in %s" % data_path)
        vocab, _ = initialize_vocabulary(vocabulary_path)
        with codecs_open(data_path, "rb", encoding="utf-8") as data_file:
            with codecs_open(target_path, "wb", encoding="utf-8") as tokens_file:
                for line in data_file:
                    token_ids = sentence_to_token_ids(line, vocab, tokenizer, bos, eos)
                    tokens_file.write(" ".join([str(tok) for tok in token_ids]) + "\n")


def read_data(source_path, target_path, attention_path, sent_len, train_size=10000, shuffle=True):
    """Read data from source and target files.

    Original taken from
    https://github.com/tensorflow/tensorflow/blob/master/tensorflow/models/rnn/translate/translate.py
    """
    _X = []
    _y = []
    _a = []
    with codecs_open(source_path, mode="r", encoding="utf-8") as source_file:
        with codecs_open(target_path, mode="r", encoding="utf-8") as target_file:
            with codecs_open(attention_path, mode="r", encoding="utf-8") as att_file:
                source, target, att = source_file.readline(), target_file.readline(), att_file.readline()
                counter = 0
                print("Loading data...")
                while source and target and att:
                    counter += 1
                    #if counter % 1000 == 0:
                    #    print("  reading data line %d" % counter)
                    #    sys.stdout.flush()
                    source_ids = [np.int64(x.strip()) for x in source.split()]
                    if sent_len > len(source_ids):
                        source_ids += [PAD_ID] * (sent_len - len(source_ids))
                    assert len(source_ids) == sent_len

                    target_ids = [np.float32(y.strip()) for y in target.split()]

                    _X.append(source_ids)
                    _y.append(target_ids)
                    _a.append(np.float32(att.strip()))
                    source, target, att = source_file.readline(), target_file.readline(), att_file.readline()


    _X = np.array(_X)
    _y = np.array(_y)
    _a = np.array(_a)
    _a_softmax = np.reshape(np.exp(_a) / np.sum(np.exp(_a)), (_y.shape[0], 1))
    #print _X.shape, _y.shape, _a_softmax.shape
    assert _X.shape[0] == _y.shape[0]
    assert _a_softmax.shape[0] == _y.shape[0]
    assert _X.shape[1] == sent_len

    print("Shuffling and splitting data...")
    # split train-test
    data = np.array(zip(_X, _y, _a_softmax))
    data_size = _y.shape[0]
    if shuffle:
        #np.random.seed(RANDOM_SEED)
        shuffle_indices = np.random.permutation(np.arange(data_size))
        shuffled_data = data[shuffle_indices]
    else:
        shuffled_data = data
    return shuffled_data[:train_size], shuffled_data[train_size:]


def batch_iter(data, batch_size, num_epochs, shuffle=True):
    """Generates a batch iterator for a dataset.

    Original taken from

    """
    data = np.array(data)
    data_size = len(data)
    num_batches_per_epoch = int(np.ceil(float(data_size)/batch_size))
    for epoch in range(num_epochs):
        # Shuffle the data at each epoch
        if shuffle:
            #np.random.seed(RANDOM_SEED)
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data = data[shuffle_indices]
        else:
            shuffled_data = data
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, data_size)
            yield shuffled_data[start_index:end_index]



def dump_to_file(filename, obj):
    with open(filename, 'wb') as outfile:
        pickle.dump(obj, file=outfile)
    return

def load_from_dump(filename):
    with open(filename, 'rb') as infile:
        obj = pickle.load(infile)
    return obj

def _load_bin_vec(fname, vocab):
    """
    Loads 300x1 word vecs from Google (Mikolov) word2vec
    """
    word_vecs = {}
    with open(fname, "rb") as f:
        header = f.readline()
        vocab_size, layer1_size = map(int, header.split())
        binary_len = np.dtype('float32').itemsize * layer1_size
        for line in xrange(vocab_size):
            word = []
            while True:
                ch = f.read(1)
                if ch == ' ':
                    word = ''.join(word)
                    break
                if ch != '\n':
                    word.append(ch)
            if word in vocab:
                word_vecs[word] = np.fromstring(f.read(binary_len), dtype='float32')
            else:
                f.read(binary_len)
    return (word_vecs, layer1_size)

def _add_random_vec(word_vecs, vocab, emb_size=300):
    for word in vocab:
        if word not in word_vecs:
            word_vecs[word] = np.random.uniform(-0.25,0.25,emb_size)
    return word_vecs

def prepare_pretrained_embedding(fname, word2id):
    print 'Reading pretrained word vectors from file ...'
    word_vecs, emb_size = _load_bin_vec(fname, word2id)
    word_vecs = _add_random_vec(word_vecs, word2id, emb_size)
    embedding = np.zeros([len(word2id), emb_size])
    for w,idx in word2id.iteritems():
        embedding[idx,:] = word_vecs[w]
    print 'Generated embeddings with shape ' + str(embedding.shape)
    return embedding



def prepare_ids(data_dir, vocab_path):
    for context in ['left', 'middle', 'right', 'txt']:
        data_path = os.path.join(data_dir, 'clean.%s' % context)
        target_path = os.path.join(data_dir, 'ids.%s' % context)
        if context == 'left':
            bos, eos = True, False
        elif context == 'middle':
            bos, eos = False, False
        elif context == 'right':
            bos, eos = False, True
        else:
            bos, eos = True, True
        data_to_token_ids(data_path, target_path, vocab_path, bos=bos, eos=eos)



def main():
    # text data
    data_dir = os.path.join(THIS_DIR, 'data')
    """
    vocab_path = os.path.join(data_dir, 'vocab.txt')
    data_path = os.path.join(data_dir, 'clean.txt')
    max_vocab_size = 40000
    create_vocabulary(vocab_path, data_path, max_vocab_size)
    prepare_ids(data_dir, vocab_path)


    # pretrained embeddings
    word2id, _ = initialize_vocabulary(vocab_path)
    embedding_path = os.path.join(THIS_DIR, 'word2vec', 'GoogleNews-vectors-negative300.bin')
    embedding = prepare_pretrained_embedding(embedding_path, word2id)
    np.save(os.path.join(data_dir, 'emb.npy'), embedding)
    """

    # er data
    vocab_er = os.path.join(data_dir, 'vocab.er')
    data_er = os.path.join(data_dir, 'clean.er')
    target_er = os.path.join(data_dir, 'ids.er')
    max_vocab_size = 8500
    tokenizer = lambda x: x.split()
    create_vocabulary(vocab_er, data_er, max_vocab_size, tokenizer=tokenizer)
    data_to_token_ids(data_er, target_er, vocab_er, tokenizer=tokenizer)


if __name__ == '__main__':
    main()