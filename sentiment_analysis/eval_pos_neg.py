#! /usr/bin/env python

import csv
import os

import numpy as np
import tensorflow as tf
from tensorflow.contrib import learn
from sentiment_analysis.data_helpers import load_data_and_labels_2_class
from sentiment_analysis.data_helpers import batch_iter
from config import config

if __name__ == '__main__':
    # Parameters
    # ==================================================

    # Data Parameters
    tf.flags.DEFINE_string("positive_data_file", config.project_path + "sentiment_analysis/data/test/test.pos",
                           "Data source for the positive data.")
    tf.flags.DEFINE_string("negative_data_file", config.project_path + "sentiment_analysis/data/test/test.neg",
                           "Data source for the negative data.")

    # Eval Parameters
    tf.flags.DEFINE_integer("batch_size", 64, "Batch Size (default: 64)")
    tf.flags.DEFINE_string("checkpoint_dir", config.project_path + "sentiment_analysis/runs/" + config.sentiment_checkpoint,
                           "Checkpoint directory from training run")
    tf.flags.DEFINE_boolean("eval_train", True, "Evaluate on all training data")

    # Misc Parameters
    tf.flags.DEFINE_boolean("allow_soft_placement", True, "Allow device soft device placement")
    tf.flags.DEFINE_boolean("log_device_placement", False, "Log placement of ops on devices")

    FLAGS = tf.flags.FLAGS

    # CHANGE THIS: Load data. Load your own data here
    if FLAGS.eval_train:
        x_raw, y_test = load_data_and_labels_2_class(FLAGS.positive_data_file,
                                                     FLAGS.negative_data_file)
        y_test = np.argmax(y_test, axis=1)
    else:
        x_raw = ["a masterpiece four years in the making", "everything is off."]
        y_test = [1, 0]

    # Map data into vocabulary
    vocab_path = os.path.join(FLAGS.checkpoint_dir, 'vocab')
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform(x_raw)))

    print('x_raw', x_raw[:10])

    print("\nEvaluating...\n")

    # Evaluation
    # ==================================================
    checkpoint_file = tf.train.latest_checkpoint(FLAGS.checkpoint_dir + '/checkpoints')
    graph = tf.Graph()
    with graph.as_default():
        session_conf = tf.ConfigProto(
            allow_soft_placement=FLAGS.allow_soft_placement,
            log_device_placement=FLAGS.log_device_placement)
        sess = tf.Session(config=session_conf)
        with sess.as_default():
            # Load the saved meta graph and restore variables
            saver = tf.train.import_meta_graph("{}.meta".format(checkpoint_file))
            saver.restore(sess, checkpoint_file)

            # Get the placeholders from the graph by name
            input_x = graph.get_operation_by_name("input_x").outputs[0]
            # input_y = graph.get_operation_by_name("input_y").outputs[0]
            dropout_keep_prob = graph.get_operation_by_name("dropout_keep_prob").outputs[0]

            # Tensors we want to evaluate
            predictions = graph.get_operation_by_name("output/predictions").outputs[0]

            # Generate batches for one epoch
            batches = batch_iter(list(x_test), FLAGS.batch_size, 1, shuffle=False)

            # Collect the predictions here
            all_predictions = []
            print('step 7', batches)
            for x_test_batch in batches:
                batch_predictions = sess.run(predictions, {input_x: x_test_batch, dropout_keep_prob: 1.0})
                print('loop: ', batch_predictions)
                all_predictions = np.concatenate([all_predictions, batch_predictions])

    # Print accuracy if y_test is defined
    if y_test is not None:
        correct_predictions = float(sum(all_predictions == y_test))
        print("Total number of test examples: {}".format(len(y_test)))
        print("Accuracy: {:g}".format(correct_predictions / float(len(y_test))))

    # Save the evaluation to a csv
    predictions_human_readable = np.column_stack((np.array(x_raw), all_predictions))
    out_path = os.path.join(FLAGS.checkpoint_dir, "..", "prediction.csv")
    print("Saving evaluation to {0}".format(out_path))
    with open(out_path, 'w') as f:
        csv.writer(f).writerows(predictions_human_readable)
