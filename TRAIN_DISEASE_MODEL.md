# How to Train Plant Disease Detection

This project now has two disease-check modes:

1. **Image analysis demo mode** — works immediately without training.
2. **Trained ML model mode** — starts automatically after you train and save the model files.

## 1. Dataset Folder Format

Create a folder named `dataset` like this:

```text
dataset/
  train/
    Tomato___healthy/
    Tomato___Late_blight/
    Potato___Early_blight/
  val/
    Tomato___healthy/
    Tomato___Late_blight/
    Potato___Early_blight/
```

Each class folder should contain many leaf images for that class.

Example class names:

```text
Tomato___healthy
Tomato___Late_blight
Tomato___Leaf_Mold
Potato___Early_blight
Potato___healthy
Apple___Apple_scab
Apple___healthy
```

## 2. Where to Get Dataset

For college project training, use a labelled dataset such as PlantVillage.

PlantVillage contains thousands of healthy and diseased plant leaf images arranged by plant and disease category.

## 3. Install AI Training Packages

Normal website running does not need TensorFlow. Training needs TensorFlow.

```bash
pip install tensorflow scikit-learn matplotlib
```

## 4. Train the Model

Keep your dataset folder inside the project root, then run:

```bash
python ai/train_model.py --data dataset --epochs 8
```

The script will create:

```text
models/plant_disease_model.keras
models/class_indices.json
```

## 5. Connect Model to Website

No extra coding is needed.

The `/detect` route already checks whether these files exist:

```text
models/plant_disease_model.keras
models/class_indices.json
```

If they are available, the website uses the trained model. If not, it uses the image-analysis demo mode.

## 6. Run Website After Training

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000/disease
```

Upload a clear leaf image and check the result.

## 7. Tips for Better Accuracy

- Use at least 300 to 500 images per class if possible.
- Keep train and validation images separate.
- Use clear close-up leaf photos.
- Do not mix different diseases inside one class folder.
- Add Indian plant examples if your project focuses on Indian home gardening.
- Test with new images that were not used during training.

## 8. Project Explanation for Viva

You can say:

> The plant disease module supports two levels. First, it has a working image-analysis demo that checks leaf colour and visible spot patterns. Second, it is model-ready. A MobileNetV2 transfer-learning CNN can be trained using a labelled dataset such as PlantVillage. Once trained, the model file is saved in the models folder, and the Flask disease route automatically uses it for predictions.
