# Convolutional Neural Network for Language Detection

**Note:** This project is mostly based on https://github.com/yuhaozhang/sentence-convnet

---


## Requirements

- [Python 2.7](https://www.python.org/)
- [Tensorflow](https://www.tensorflow.org/) (tested with version 0.10.0rc0)
- [Numpy](http://www.numpy.org/)

To download wikipedia articles

- [Beautifulsoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Pandas](http://pandas.pydata.org/)


## Data
- `data` directory includes preprocessed data:
- `word2vec` directory is empty. Please download 

    ```
    cnn-re-tf
    ├── ...
    ├── word2vec
    └── data
        ├── clean.att   # attention
        ├── clean.label # label (class names)
        └── clean.txt   # raw sentences

        
    ```    


## Preprocess

```sh
python ./util.py
```

## Training

```sh
python ./train.py --train_dir=./train --data_dir=./data
```


## Evaluation

```sh
python ./eval.py --train_dir=./train/1473898241
```

## Run TensorBoard

```sh
tensorboard --logdir=./train/1473898241
```


## References

Implementation:

* https://github.com/yuhaozhang/sentence-convnet
* https://github.com/dennybritz/cnn-text-classification-tf
* http://www.wildml.com/2015/12/implementing-a-cnn-for-text-classification-in-tensorflow/
* http://tkengo.github.io/blog/2016/03/14/text-classification-by-cnn/

Theory:
* 
* 
* 

