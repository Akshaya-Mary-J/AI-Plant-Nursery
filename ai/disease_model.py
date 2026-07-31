"""Plant disease prediction helper.

This file works in two modes:
1. Trained-model mode: if models/plant_disease_model.keras and
   models/class_indices.json exist, TensorFlow is used for prediction.
2. Demo fallback mode: if no trained model exists, the uploaded image is
   analysed using colour/spot heuristics so the feature still works during
   college demonstration.
"""

from __future__ import annotations
import json
import os
from functools import lru_cache
from typing import Dict, Tuple

import numpy as np
from PIL import Image, ImageStat

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH = os.path.join(BASE_DIR, "models", "plant_disease_model.keras")
CLASS_INDEX_PATH = os.path.join(BASE_DIR, "models", "class_indices.json")
IMAGE_SIZE = (224, 224)

ADVICE_MAP: Dict[str, str] = {
    "healthy": "The leaf looks healthy. Keep the plant in suitable light, water only when required, and check leaves weekly.",
    "leaf spot": "Possible leaf spot detected. Remove affected leaves, avoid watering on leaves, improve airflow, and use an organic fungicide if the issue spreads.",
    "blight": "Possible blight symptom detected. Isolate the plant, cut infected parts, avoid overhead watering, and keep the plant in airy indirect light.",
    "rust": "Possible rust-like infection detected. Remove infected leaves and keep foliage dry. Use suitable fungicide if symptoms continue.",
    "powdery mildew": "Possible powdery mildew detected. Improve ventilation, avoid overcrowding, and remove heavily affected leaves.",
    "yellow": "Yellowing may be due to overwatering, low sunlight, or nutrient deficiency. Let soil dry slightly and give bright indirect light.",
}


def _safe_advice(label: str) -> str:
    clean = label.lower().replace("_", " ").replace("-", " ")
    for key, advice in ADVICE_MAP.items():
        if key in clean:
            return advice
    return "Prediction completed. Compare the symptoms with the plant condition and consult a local nursery expert for severe infection."


@lru_cache(maxsize=1)
def _load_trained_model():
    """Load TensorFlow model only when model files are available."""
    if not (os.path.exists(MODEL_PATH) and os.path.exists(CLASS_INDEX_PATH)):
        return None, None
    try:
        import tensorflow as tf  # Optional dependency for trained model mode

        model = tf.keras.models.load_model(MODEL_PATH)
        with open(CLASS_INDEX_PATH, "r", encoding="utf-8") as f:
            class_indices = json.load(f)
        labels = {int(v): k for k, v in class_indices.items()}
        return model, labels
    except Exception:
        # Keep project working even when TensorFlow is not installed.
        return None, None


def _predict_with_trained_model(image_path: str):
    model, labels = _load_trained_model()
    if model is None or labels is None:
        return None

    image = Image.open(image_path).convert("RGB").resize(IMAGE_SIZE)
    arr = np.asarray(image, dtype="float32") / 255.0
    arr = np.expand_dims(arr, axis=0)
    preds = model.predict(arr, verbose=0)[0]
    idx = int(np.argmax(preds))
    confidence = float(preds[idx])
    label = labels.get(idx, "Unknown plant condition")
    return {
        "disease": label.replace("___", " - ").replace("_", " ").title(),
        "confidence": f"{confidence * 100:.2f}%",
        "advice": _safe_advice(label),
        "mode": "Trained ML model",
    }


def _leaf_colour_analysis(image_path: str) -> Tuple[str, str, str]:
    """Fallback analysis based on visible colour and spot patterns.

    This is not a medical/agricultural diagnosis. It gives a believable,
    functional final-year-project demo until a real CNN model is trained.
    """
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((480, 480))
    arr = np.asarray(image, dtype=np.float32)

    if arr.size == 0:
        return "Image could not be analysed", "0%", "Please upload a clear JPG/PNG leaf image."

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    brightness = (r + g + b) / 3.0
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    saturation = (maxc - minc) / np.maximum(maxc, 1)

    # Ignore plain white/black background as much as possible.
    candidate_leaf = (saturation > 0.12) & (brightness > 25) & (brightness < 245)
    green = candidate_leaf & (g > r * 1.06) & (g > b * 1.04)
    yellow = candidate_leaf & (r > 105) & (g > 95) & (b < 125) & (np.abs(r - g) < 85)
    brown = candidate_leaf & (r > 55) & (g > 30) & (b < 105) & (r >= g * 0.75) & (g >= b * 0.75)
    dark_spots = candidate_leaf & (brightness < 72) & (saturation > 0.18)
    pale_mildew = candidate_leaf & (brightness > 180) & (saturation < 0.20)

    leaf_pixels = max(1, int(candidate_leaf.sum()))
    leaf_ratio = leaf_pixels / arr.shape[0] / arr.shape[1]
    green_ratio = float(green.sum() / leaf_pixels)
    yellow_ratio = float(yellow.sum() / leaf_pixels)
    brown_ratio = float(brown.sum() / leaf_pixels)
    dark_ratio = float(dark_spots.sum() / leaf_pixels)
    mildew_ratio = float(pale_mildew.sum() / leaf_pixels)

    # Basic blur check to guide student/user.
    stat = ImageStat.Stat(image.convert("L"))
    contrast = stat.stddev[0]

    if leaf_ratio < 0.03:
        return (
            "Leaf not clearly detected",
            "Low",
            "Please upload a close-up photo of one leaf against a plain background with good lighting.",
        )
    if contrast < 18:
        return (
            "Image is too blurred for reliable checking",
            "Low",
            "Retake the leaf photo in better light and keep the camera steady.",
        )
    if yellow_ratio > 0.18 and green_ratio < 0.50:
        return (
            "Yellowing leaf symptom",
            "Demo confidence: 68%",
            "Yellowing is commonly caused by overwatering, low sunlight, or nutrient deficiency. Check drainage and water only when top soil is dry.",
        )
    if brown_ratio > 0.06 or dark_ratio > 0.06:
        return (
            "Possible fungal leaf spot or blight symptom",
            "Demo confidence: 72%",
            "Remove infected leaves, avoid spraying water on leaves, improve airflow, and keep the plant away from other plants for a few days.",
        )
    if mildew_ratio > 0.22 and green_ratio < 0.30:
        return (
            "Possible powdery mildew or pale fungal growth",
            "Demo confidence: 66%",
            "Wipe affected leaves gently, improve ventilation, avoid overcrowding, and do not keep leaves wet overnight.",
        )
    if green_ratio > 0.35 and brown_ratio < 0.08 and yellow_ratio < 0.16:
        return (
            "Leaf looks mostly healthy",
            "Demo confidence: 75%",
            "The uploaded leaf appears mostly healthy. Continue proper watering, sunlight, and monthly observation.",
        )
    return (
        "Basic visual check completed",
        "Demo confidence: 58%",
        "No strong disease pattern was detected. For accurate disease identification, train and connect the CNN model using the included training guide.",
    )


def predict_leaf_disease(image_path: str) -> Dict[str, str]:
    trained_result = _predict_with_trained_model(image_path)
    if trained_result:
        return trained_result
    disease, confidence, advice = _leaf_colour_analysis(image_path)
    return {"disease": disease, "confidence": confidence, "advice": advice, "mode": "Image analysis demo"}
