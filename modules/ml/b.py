from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout


def build_model(input_dim, layers, activation='relu', optimizer='adam'):
    model = Sequential()
    model.add(Dense(layers[0], activation=activation, input_shape=(input_dim,)))
    for units in layers[1:]:
        model.add(Dense(units, activation=activation))
        model.add(Dropout(0.3))
    model.add(Dense(3, activation='softmax'))

    model.compile(optimizer=optimizer,
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    return model
