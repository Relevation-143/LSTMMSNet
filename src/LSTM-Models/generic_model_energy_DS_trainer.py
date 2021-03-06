import numpy as np
import tensorflow as tf
import argparse
from utility_scripts.persist_optimized_config_results import persist_results
from generic_mean_m4hourly_test import testing
import re
import random
import time

# import the config space and the different types of parameters
from smac.configspace import ConfigurationSpace
from ConfigSpace.hyperparameters import UniformFloatHyperparameter, UniformIntegerHyperparameter

# import SMAC utilities
from smac.scenario.scenario import Scenario
from smac.facade.smac_facade import SMAC

## import the different model architectures

# stacking model
from rnn_architectures.stacking_model.stacking_mean_model_trainer import \
    StackingModelTrainer as StackingModelTrainer

# seq2seq model with decoder
from rnn_architectures.seq2seq_model.with_decoder.non_moving_window.seq2seq_model_trainer import \
    Seq2SeqModelTrainer as Seq2SeqModelTrainerWithNonMovingWindow

# seq2seq model with dense layer
from rnn_architectures.seq2seq_model.with_dense_layer.non_moving_window.seq2seq_model_trainer import \
    Seq2SeqModelTrainerWithDenseLayer as Seq2SeqModelTrainerWithDenseLayerNonMovingWindow
from rnn_architectures.seq2seq_model.with_dense_layer.moving_window.seq2seq_mean_model_trainer import \
    Seq2SeqModelTrainerWithDenseLayer as Seq2SeqModelTrainerWithDenseLayerMovingWindow

# attention model
from rnn_architectures.attention_model.bahdanau_attention.with_stl_decomposition.non_moving_window.attention_model_trainer import \
    AttentionModelTrainer as AttentionModelTrainerWithNonMovingWindowWithoutSeasonality
from rnn_architectures.attention_model.bahdanau_attention.without_stl_decomposition.non_moving_window.attention_model_trainer import \
    AttentionModelTrainer as AttentionModelTrainerWithNonMovingWindowWithSeasonality

# import the cocob optimizer
from external_packages import cocob_optimizer

from configs.global_configs import hyperparameter_tuning_configs

LSTM_USE_PEEPHOLES = True
BIAS = False

optimized_config_directory = 'results/optimized_configurations/'
learning_rate = 0.0


# learning_rate_decay = 0.0

# function to create the optimizer
def adagrad_optimizer_fn(total_loss):
    # global_step = tf.Variable(0, trainable=False)
    # rate = tf.train.exponential_decay(learning_rate=learning_rate, global_step=global_step, decay_steps=1, decay_rate=learning_rate_decay)
    return tf.train.AdagradOptimizer(learning_rate=learning_rate).minimize(total_loss)


def adam_optimizer_fn(total_loss):
    # global_step = tf.Variable(0, trainable=False)
    # rate = tf.train.exponential_decay(learning_rate=learning_rate, global_step=global_step, decay_steps=1,
    #                                   decay_rate=learning_rate_decay)
    return tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(total_loss)


def cocob_optimizer_fn(total_loss):
    return cocob_optimizer.COCOB().minimize(loss=total_loss)


def read_initial_hyperparameter_values():
    # define dictionary to store the hyperparameter values
    hyperparameter_values_dic = {}

    with open(initial_hyperparameter_values_file) as configs_file:
        configs = configs_file.readlines()
        for config in configs:
            if not config.startswith('#') and config.strip():
                values = [value.strip() for value in (re.split("-|,", config))]
                hyperparameter_values_dic[values[0]] = [float(values[1]), float(values[2])]

        configs_file.close()

    return hyperparameter_values_dic


def read_optimal_hyperparameter_values(file_name):
    # define dictionary to store the hyperparameter values
    hyperparameter_values_dic = {}

    with open(file_name) as configs_file:
        configs = configs_file.readlines()
        for config in configs:
            if not config.startswith('#') and config.strip():
                values = [value.strip() for value in (re.split(">>>", config))]
                hyperparameter_values_dic[values[0]] = float(values[1])

        configs_file.close()

    return hyperparameter_values_dic


# Training the time series
def train_model_smac(configs):
    rate_of_learning = configs["rate_of_learning"]
    # rate_of_decay = configs["rate_of_decay"]
    cell_dimension = configs["cell_dimension"]
    num_hidden_layers = configs["num_hidden_layers"]
    minibatch_size = configs["minibatch_size"]
    max_epoch_size = configs["max_epoch_size"]
    max_num_epochs = configs["max_num_epochs"]
    l2_regularization = configs["l2_regularization"]
    gaussian_noise_stdev = configs["gaussian_noise_stdev"]
    random_normal_initializer_stdev = configs["random_normal_initializer_stdev"]

    global learning_rate
    learning_rate = rate_of_learning

    # global learning_rate_decay
    # learning_rate_decay = rate_of_decay

    print(configs)

    # select the appropriate type of optimizer
    error = model_trainer.train_model(num_hidden_layers=num_hidden_layers,
                                      cell_dimension=cell_dimension,
                                      minibatch_size=minibatch_size,
                                      max_epoch_size=max_epoch_size,
                                      max_num_epochs=max_num_epochs,
                                      l2_regularization=l2_regularization,
                                      gaussian_noise_stdev=gaussian_noise_stdev,
                                      random_normal_initializer_stdev=random_normal_initializer_stdev,
                                      optimizer_fn=optimizer_fn)

    print(model_identifier)
    return error


# def train_model_bayesian(num_hidden_layers, cell_dimension, minibatch_size, max_epoch_size, max_num_epochs,
#                          l2_regularization, gaussian_noise_stdev,
#                          random_normal_initializer_stdev, rate_of_learning=0.0, tbptt_chunk_length=0):
#     global learning_rate
#     learning_rate = rate_of_learning
#
#     error = model_trainer.train_model(num_hidden_layers=int(round(num_hidden_layers)),
#                                       cell_dimension=int(round(cell_dimension)),
#                                       minibatch_size=int(round(minibatch_size)),
#                                       max_epoch_size=int(round(max_epoch_size)),
#                                       max_num_epochs=int(round(max_num_epochs)),
#                                       l2_regularization=l2_regularization,
#                                       gaussian_noise_stdev=gaussian_noise_stdev,
#                                       random_normal_initializer_stdev=random_normal_initializer_stdev,
#                                       tbptt_chunk_length=tbptt_chunk_length,
#                                       optimizer_fn=optimizer_fn)
#     return -1 * error


# def bayesian_optimization():
#
#     init_points = hyperparameter_tuning_configs.BAYESIAN_INIT_POINTS
#     num_iter = hyperparameter_tuning_configs.BAYESIAN_NUM_ITER
#     gaussian_process_parameters = {'alpha': 1e-4}
#
#     parameters = {'num_hidden_layers': (
#         hyperparameter_values_dic['num_hidden_layers'][0], hyperparameter_values_dic['num_hidden_layers'][1]),
#         'cell_dimension': (hyperparameter_values_dic['cell_dimension'][0],
#                                 hyperparameter_values_dic['cell_dimension'][1]),
#         'minibatch_size': (
#             hyperparameter_values_dic['minibatch_size'][0], hyperparameter_values_dic['minibatch_size'][1]),
#         'max_epoch_size': (
#             hyperparameter_values_dic['max_epoch_size'][0], hyperparameter_values_dic['max_epoch_size'][1]),
#         'max_num_epochs': (
#             hyperparameter_values_dic['max_num_epochs'][0], hyperparameter_values_dic['max_num_epochs'][1]),
#         'l2_regularization': (
#             hyperparameter_values_dic['l2_regularization'][0], hyperparameter_values_dic['l2_regularization'][1]),
#         'gaussian_noise_stdev': (hyperparameter_values_dic['gaussian_noise_stdev'][0],
#                                  hyperparameter_values_dic['gaussian_noise_stdev'][1]),
#         'random_normal_initializer_stdev': (hyperparameter_values_dic['random_normal_initializer_stdev'][0],
#                                             hyperparameter_values_dic['random_normal_initializer_stdev'][1])
#     }
#
#     # adding the hyperparameter for learning rate if the optimization is not cocob
#     if optimizer != 'cocob':
#         parameters['rate_of_learning'] = (
#             hyperparameter_values_dic["rate_of_learning"][0], hyperparameter_values_dic["rate_of_learning"][1])
#     if with_truncated_backpropagation:
#         parameters['tbptt_chunk_length'] = (
#             hyperparameter_values_dic["tbptt_chunk_length"][0], hyperparameter_values_dic["tbptt_chunk_length"][1])
#
#     # using bayesian optimizer for hyperparameter optimization
#     bayesian_optimization = BayesianOptimization(train_model_bayesian, parameters)
#
#     bayesian_optimization.maximize(init_points=init_points, n_iter=num_iter, **gaussian_process_parameters)
#     optimized_configuration = bayesian_optimization.res['max']['max_params']
#     print(optimized_configuration)
#
#     return optimized_configuration


def smac():
    # Build Configuration Space which defines all parameters and their ranges
    configuration_space = ConfigurationSpace()

    rate_of_learning = UniformFloatHyperparameter("rate_of_learning", hyperparameter_values_dic['rate_of_learning'][0],
                                                  hyperparameter_values_dic['rate_of_learning'][1],
                                                  default_value=hyperparameter_values_dic['rate_of_learning'][0])
    # rate_of_decay = UniformFloatHyperparameter("rate_of_decay", hyperparameter_values_dic['rate_of_decay'][0],
    #                                               hyperparameter_values_dic['rate_of_decay'][1],
    #                                               default_value=hyperparameter_values_dic['rate_of_decay'][1])
    cell_dimension = UniformIntegerHyperparameter("cell_dimension",
                                                  hyperparameter_values_dic['cell_dimension'][0],
                                                  hyperparameter_values_dic['cell_dimension'][1],
                                                  default_value=hyperparameter_values_dic['cell_dimension'][
                                                      0])
    no_hidden_layers = UniformIntegerHyperparameter("num_hidden_layers",
                                                    hyperparameter_values_dic['num_hidden_layers'][0],
                                                    hyperparameter_values_dic['num_hidden_layers'][1],
                                                    default_value=hyperparameter_values_dic['num_hidden_layers'][0])
    minibatch_size = UniformIntegerHyperparameter("minibatch_size", hyperparameter_values_dic['minibatch_size'][0],
                                                  hyperparameter_values_dic['minibatch_size'][1],
                                                  default_value=hyperparameter_values_dic['minibatch_size'][0])
    max_epoch_size = UniformIntegerHyperparameter("max_epoch_size", hyperparameter_values_dic['max_epoch_size'][0],
                                                  hyperparameter_values_dic['max_epoch_size'][1],
                                                  default_value=hyperparameter_values_dic['max_epoch_size'][0])
    max_num_of_epochs = UniformIntegerHyperparameter("max_num_epochs", hyperparameter_values_dic['max_num_epochs'][0],
                                                     hyperparameter_values_dic['max_num_epochs'][1],
                                                     default_value=hyperparameter_values_dic['max_num_epochs'][0])
    l2_regularization = UniformFloatHyperparameter("l2_regularization",
                                                   hyperparameter_values_dic['l2_regularization'][0],
                                                   hyperparameter_values_dic['l2_regularization'][1],
                                                   default_value=hyperparameter_values_dic['l2_regularization'][0])
    gaussian_noise_stdev = UniformFloatHyperparameter("gaussian_noise_stdev",
                                                      hyperparameter_values_dic['gaussian_noise_stdev'][0],
                                                      hyperparameter_values_dic['gaussian_noise_stdev'][1],
                                                      default_value=hyperparameter_values_dic['gaussian_noise_stdev'][
                                                          0])
    random_normal_initializer_stdev = UniformFloatHyperparameter("random_normal_initializer_stdev",
                                                                 hyperparameter_values_dic[
                                                                     'random_normal_initializer_stdev'][0],
                                                                 hyperparameter_values_dic[
                                                                     'random_normal_initializer_stdev'][1],
                                                                 default_value=hyperparameter_values_dic[
                                                                     'random_normal_initializer_stdev'][
                                                                     0])

    # add the hyperparameter for learning rate only if the  optimization is not cocob
    if optimizer == "cocob":
        configuration_space.add_hyperparameters(
            [cell_dimension, no_hidden_layers, minibatch_size, max_epoch_size, max_num_of_epochs,
             l2_regularization, gaussian_noise_stdev, random_normal_initializer_stdev])
    else:

        configuration_space.add_hyperparameters(
            [rate_of_learning, cell_dimension, no_hidden_layers, minibatch_size, max_epoch_size,
             max_num_of_epochs,
             l2_regularization, gaussian_noise_stdev, random_normal_initializer_stdev])

    # creating the scenario object
    scenario = Scenario({
        "run_obj": "quality",
        "runcount-limit": hyperparameter_tuning_configs.SMAC_RUNCOUNT_LIMIT,
        "cs": configuration_space,
        "deterministic": "true",
        "abort_on_first_run_crash": "false"
    })

    # optimize using an SMAC object
    smac = SMAC(scenario=scenario, rng=np.random.RandomState(seed), tae_runner=train_model_smac)

    incumbent = smac.optimize()
    smape_error = train_model_smac(incumbent)

    print("Optimized configuration: {}".format(incumbent))
    print("Optimized Value: {}\n".format(smape_error))
    return incumbent.get_dictionary()


if __name__ == '__main__':
    start = time.time()

    argument_parser = argparse.ArgumentParser("Train different forecasting models")
    argument_parser.add_argument('--dataset_name', required=True, help='Unique string for the name of the dataset')
    argument_parser.add_argument('--contain_zero_values', required=True,
                                 help='Whether the dataset contains zero values(0/1)')
    argument_parser.add_argument('--initial_hyperparameter_values_file', required=True,
                                 help='The file for the initial hyperparameter configurations')
    argument_parser.add_argument('--binary_train_file_train_mode', required=True,
                                 help='The tfrecords file for train dataset in the training mode')
    argument_parser.add_argument('--binary_valid_file_train_mode', required=True,
                                 help='The tfrecords file for validation dataset in the training mode')
    argument_parser.add_argument('--binary_train_file_test_mode', required=True,
                                 help='The tfrecords file for train dataset in the testing mode')
    argument_parser.add_argument('--binary_test_file_test_mode', required=True,
                                 help='The tfrecords file for test dataset in the testing mode')
    argument_parser.add_argument('--txt_test_file', required=True, help='The txt file for test dataset')
    argument_parser.add_argument('--actual_results_file', required=True, help='The txt file of the actual results')
    argument_parser.add_argument('--cell_type', required=False,
                                 help='The cell type of the RNN(LSTM/GRU). Default is LSTM')
    argument_parser.add_argument('--input_size', required=False,
                                 help='The input size of the moving window. Default is 0')
    argument_parser.add_argument('--forecast_horizon', required=True, help='The forecast horizon of the dataset')
    argument_parser.add_argument('--optimizer', required=True, help='The type of the optimizer(cocob/adam/adagrad...)')
    argument_parser.add_argument('--hyperparameter_tuning', required=True,
                                 help='The method for hyperparameter tuning(bayesian/smac)')
    argument_parser.add_argument('--model_type', required=True,
                                 help='The type of the model(stacking/seq2seq/seq2seqwithdenselayer/attention)')
    argument_parser.add_argument('--input_format', required=True, help='Input format(moving_window/non_moving_window)')
    argument_parser.add_argument('--without_stl_decomposition', required=False,
                                 help='Whether not to use stl decomposition(0/1). Default is 0')
    argument_parser.add_argument('--with_truncated_backpropagation', required=False,
                                 help='Whether not to use truncated backpropagation(0/1). Default is 0')
    argument_parser.add_argument('--seed', required=True, help='Integer seed to use as the random seed')

    # parse the user arguments
    args = argument_parser.parse_args()

    dataset_name = args.dataset_name
    initial_hyperparameter_values_file = args.initial_hyperparameter_values_file
    binary_train_file_path_train_mode = args.binary_train_file_train_mode
    binary_validation_file_path_train_mode = args.binary_valid_file_train_mode
    contain_zero_values = int(args.contain_zero_values)

    if args.input_size:
        input_size = int(args.input_size)
    else:
        input_size = 0

    output_size = int(args.forecast_horizon)
    optimizer = args.optimizer
    hyperparameter_tuning = args.hyperparameter_tuning
    model_type = args.model_type
    input_format = args.input_format
    seed = int(args.seed)

    if args.without_stl_decomposition:
        without_stl_decomposition = bool(int(args.without_stl_decomposition))
    else:
        without_stl_decomposition = False

    if args.with_truncated_backpropagation:
        with_truncated_backpropagation = bool(int(args.with_truncated_backpropagation))
    else:
        with_truncated_backpropagation = False

    if args.cell_type:
        cell_type = args.cell_type
    else:
        cell_type = "LSTM"

    if with_truncated_backpropagation:
        tbptt_identifier = "with_truncated_backpropagation"
    else:
        tbptt_identifier = "without_truncated_backpropagation"

    if without_stl_decomposition:
        stl_decomposition_identifier = "without_stl_decomposition"
    else:
        stl_decomposition_identifier = "with_stl_decomposition"

    model_identifier = dataset_name + "_" + model_type + "_" + cell_type + "cell" + "_" + input_format + "_" + stl_decomposition_identifier + "_" + hyperparameter_tuning + "_" + optimizer + "_" + tbptt_identifier + "_" + str(
        seed)
    print("Model Training Started for {}".format(model_identifier))

    # select the optimizer
    if optimizer == "cocob":
        optimizer_fn = cocob_optimizer_fn
    elif optimizer == "adagrad":
        optimizer_fn = adagrad_optimizer_fn
    elif optimizer == "adam":
        optimizer_fn = adam_optimizer_fn

    # define the key word arguments for the different model types
    model_kwargs = {
        'use_bias': BIAS,
        'use_peepholes': LSTM_USE_PEEPHOLES,
        'input_size': input_size,
        'output_size': output_size,
        'binary_train_file_path': binary_train_file_path_train_mode,
        'binary_validation_file_path': binary_validation_file_path_train_mode,
        'contain_zero_values': contain_zero_values,
        'seed': seed,
        'cell_type': cell_type
    }

    # select the model type
    if model_type == "stacking":
        model_trainer = StackingModelTrainer(**model_kwargs)
    elif model_type == "seq2seq":
        model_trainer = Seq2SeqModelTrainerWithNonMovingWindow(**model_kwargs)
    elif model_type == "seq2seqwithdenselayer":
        if input_format == "non_moving_window":
            model_trainer = Seq2SeqModelTrainerWithDenseLayerNonMovingWindow(**model_kwargs)
        elif input_format == "moving_window":
            model_trainer = Seq2SeqModelTrainerWithDenseLayerMovingWindow(**model_kwargs)
    elif model_type == "attention":
        if without_stl_decomposition:
            model_trainer = AttentionModelTrainerWithNonMovingWindowWithSeasonality(**model_kwargs)
        else:
            model_trainer = AttentionModelTrainerWithNonMovingWindowWithoutSeasonality(**model_kwargs)

    # read the initial hyperparamter configurations from the file
    hyperparameter_values_dic = read_initial_hyperparameter_values()

    # select the hyperparameter tuning method
    # if hyperparameter_tuning == "bayesian":
    #     optimized_configuration = bayesian_optimization()
    # elif hyperparameter_tuning == "smac"

    optimized_configuration = smac()

    #NN5 configs
    #optimized_configuration = {
    #     "num_hidden_layers": 1,
    #    "cell_dimension": 29,
    #     "minibatch_size": 46,
    #     "max_epoch_size": 1,
    #    "gaussian_noise_stdev": 0.000773898696114539,
    #     "l2_regularization": 0.0003030977909805427,
    #     "max_num_epochs": 7,
    #     "random_normal_initializer_stdev": 0.0006821503256269937
    # }


    # NN3 configs
    #optimized_configuration = {
     #    "num_hidden_layers": 1,
      #   "cell_dimension": 21,
       #  "minibatch_size": 46,
        # "max_epoch_size": 5,
        # "gaussian_noise_stdev": 0.00034138656903286683,
        # "l2_regularization": 0.00012930912491313084,
        # "max_num_epochs": 13,
        #"random_normal_initializer_stdev": 0.00015558968132129314
    # }

    # CIF configs
    # optimized_configuration = {
    #     "num_hidden_layers": 1.075789638829622,
    #     "cell_dimension": 29,
    #     "minibatch_size": 20.846339868432239,
    #     "rate_of_learning": 0.0043262220421187676,
    #     "max_epoch_size": 1,
    #     "gaussian_noise_stdev": 0.0008,
    #     "l2_regularization": 0.0001,
    #     "max_num_epochs": 19,
    #     "random_normal_initializer_stdev": 0.00027502494731703717,
    #     'tbptt_chunk_length': 10
    # }

    # 0.0910382749239466
    # CIF configs 2
    # optimized_configuration = {
    #     "num_hidden_layers": 1.075789638829622,
    #     "cell_dimension": 22,
    #     "minibatch_size": 20.846339868432239,
    #     "rate_of_learning": 0.53262220421187676,
    #     "max_epoch_size": 5,
    #     "gaussian_noise_stdev": 0.0005539332088020351,
    #     "l2_regularization": 0.0006101647564088497,
    #     "max_num_epochs": 20,
    #     "random_normal_initializer_stdev": 0.00027502494731703717
    # }

    # CIF configs 2
    # optimized_configuration = {
    #     "num_hidden_layers": 2,
    #     "cell_dimension": 28,
    #     "minibatch_size": 3,
    #     "rate_of_learning": 0.26343183932470754,
    #     "max_epoch_size": 3,
    #     "gaussian_noise_stdev": 0.0007517656514955944,
    #     "l2_regularization": 0.00022259525510874703,
    #     "max_num_epochs": 14,
    #     "random_normal_initializer_stdev": 0.0005827304210740794
    # }

    # cif
    # optimized_configuration = {'num_hidden_layers': 5.0, 'cell_dimension': 28.471127262736434,
    #                            'minibatch_size': 10.135034205224617, 'max_epoch_size': 9.1502825822926326,
    #                            'max_num_epochs': 20.962475980675006, 'l2_regularization': 0.0006369387641617046,
    #                            'gaussian_noise_stdev': 0.00057001364478555087,
    #                            'random_normal_initializer_stdev': 0.00025797511482927632,
    #                            'rate_of_learning': 0.20172634121590136}

    # persist the optimized configuration to a file
    persist_results(optimized_configuration, optimized_config_directory + '/' + model_identifier + '.txt')

    #optimized_configuration = read_optimal_hyperparameter_values(optimized_config_directory + '/' + model_identifier + '.txt')

    # test the model
    #for i in range(1, 11):
     #   args.seed = i
    testing(args, optimized_configuration)

    end = time.time()
    print(end - start)
