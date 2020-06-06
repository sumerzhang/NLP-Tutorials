"""
reference:
https://zhuanlan.zhihu.com/p/49271699
https://jalammar.github.io/illustrated-bert/
"""

import tensorflow as tf
import utils
import time
from BERT_self_mask import BERT
import pickle
import os

MODEL_DIM = 128
N_LAYER = 4
BATCH_SIZE = 12
LEARNING_RATE = 1e-4


class BERT1(BERT):
    def __init__(self, model_dim, max_len, n_layer, n_head, n_vocab, lr, max_seg=3, drop_rate=0.1, padding_idx=0):
        super().__init__(model_dim, max_len, n_layer, n_head, n_vocab, lr, max_seg, drop_rate, padding_idx)

    def mask(self, seqs):
        """
         abcd--
        a100011
        b010011
        c001011
        d000101
        -000010
        -000001
        """
        eye = tf.eye(self.max_len, batch_shape=[len(seqs)], dtype=tf.float32)
        pad = tf.math.equal(seqs, self.padding_idx)
        mask = tf.where(pad[:, tf.newaxis, tf.newaxis, :], 1, eye[:, tf.newaxis, :, :])
        return mask  # [n, 1, step, step]


def main():
    # get and process data
    data = utils.MRPCData("./MRPC", rows=2000)
    print("num word: ", data.num_word)
    model = BERT1(
        model_dim=MODEL_DIM, max_len=data.max_len, n_layer=N_LAYER, n_head=4, n_vocab=data.num_word,
        lr=LEARNING_RATE, max_seg=data.num_seg, drop_rate=0.1, padding_idx=data.pad_id)
    t0 = time.time()
    for t in range(5000):
        seqs, segs, xlen, nsp_labels = data.sample(BATCH_SIZE)
        loss, pred = model.step(seqs, segs, seqs, nsp_labels)
        if t % 50 == 0:
            pred = pred[0].numpy().argmax(axis=1)
            t1 = time.time()
            print(
                "\n\nstep: ", t,
                "| time: %.2f" % (t1 - t0),
                "| loss: %.3f" % loss.numpy(),
                "\n| tgt: ", " ".join([data.i2v[i] for i in seqs[0][:xlen[0].sum()+1]]),
                "\n| prd: ", " ".join([data.i2v[i] for i in pred[:xlen[0].sum()+1]]),
                )
            t0 = t1
    os.makedirs("./visual_helper/bert1", exist_ok=True)
    model.save_weights("./visual_helper/bert1/model.ckpt")


def export_attention():
    data = utils.MRPCData("./MRPC", rows=2000)
    print("num word: ", data.num_word)
    model = BERT1(
        model_dim=MODEL_DIM, max_len=data.max_len, n_layer=N_LAYER, n_head=4, n_vocab=data.num_word,
        lr=LEARNING_RATE, max_seg=data.num_seg, drop_rate=0.1, padding_idx=data.pad_id)
    model.load_weights("./visual_helper/bert1/model.ckpt")

    # save attention matrix for visualization
    seqs, segs, xlen, nsp_labels = data.sample(32)
    model(seqs, segs, False)
    data = {"src": [[data.i2v[i] for i in seqs[j]] for j in range(len(seqs))], "attentions": model.attentions}
    with open("./visual_helper/bert1_attention_matrix.pkl", "wb") as f:
        pickle.dump(data, f)


if __name__ == "__main__":
    main()
    export_attention()
