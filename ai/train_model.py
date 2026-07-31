"""Train a plant disease CNN model with transfer learning.

Folder format expected:

dataset/
  train/
    Apple___Apple_scab/
    Apple___healthy/
    Tomato___Late_blight/
  val/
    Apple___Apple_scab/
    Apple___healthy/
    Tomato___Late_blight/

After training, this script saves:
- models/plant_disease_model.keras
- models/class_indices.json
"""

from __future__ import annotations

import argparse
import json
import os


def train(data_dir: str, epochs: int = 8, batch_size: int = 32):
    import tensorflow as tf

    image_size = (224, 224)
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")

    if not os.path.isdir(train_dir) or not os.path.isdir(val_dir):
        raise FileNotFoundError(
            "Dataset must contain train and val folders. Example: dataset/train/ClassName and dataset/val/ClassName"
        )

    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        image_size=image_size,
        batch_size=batch_size,
        label_mode="categorical",
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        val_dir,
        image_size=image_size,
        batch_size=batch_size,
        label_mode="categorical",
    )

    class_names = train_ds.class_names
    class_indices = {name: idx for idx, name in enumerate(class_names)}

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    data_augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.08),
        tf.keras.layers.RandomZoom(0.12),
    ])

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = data_augmentation(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    outputs = tf.keras.layers.Dense(len(class_names), activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0008),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.fit(train_ds, validation_data=val_ds, epochs=epochs)

    # Fine-tune the last layers for better accuracy.
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.00005),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(train_ds, validation_data=val_ds, epochs=max(2, epochs // 2))

    os.makedirs("models", exist_ok=True)
    model.save("models/plant_disease_model.keras")
    with open("models/class_indices.json", "w", encoding="utf-8") as f:
        json.dump(class_indices, f, indent=2)

    print("Training completed.")
    print("Saved: models/plant_disease_model.keras")
    print("Saved: models/class_indices.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="dataset", help="Dataset folder containing train and val folders")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    train(args.data, args.epochs, args.batch_size)
