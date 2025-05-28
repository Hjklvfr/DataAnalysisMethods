from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam, SGD


def build_model(input_dim, layers, activation='relu', optimizer='adam'):
    model = Sequential()
    model.add(Dense(layers[0], activation=activation, input_shape=(input_dim,)))
    for units in layers[1:]:
        model.add(Dense(units, activation=activation))
        model.add(Dropout(0.3))
    model.add(Dense(1, activation='sigmoid'))

    if optimizer == 'adam':
        opt = Adam()
    elif optimizer == 'sgd':
        opt = SGD(momentum=0.9)

    model.compile(optimizer=opt, loss='binary_crossentropy', metrics=['accuracy'])
    return model
