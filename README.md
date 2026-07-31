# Akshaya AI Plant Shop

A professional Flask-based final year project for an AI plant nursery / plant shop.

## Features

- Responsive plant-themed UI
- Home page, shop page, details page, cart and checkout
- 24 seeded plants with prices, stock and correct care information
- Search, category filter and price sort
- LocalStorage shopping cart
- Cash on Delivery order placement
- Razorpay payment-ready integration
- Admin login and plant CRUD
- Plant request form
- Contact form
- AI chatbot with rule-based plant care answers
- Voice assistant using browser Web Speech API
- Plant disease check using image upload with demo analysis and trained-model support
- Watering reminder demo using LocalStorage

## Default Admin Login

Username: `admin`  
Password: `admin123`

Change these before final hosting:

```bash
set ADMIN_USERNAME=yourname
set ADMIN_PASSWORD=strongpassword
```

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Razorpay Setup

Install dependencies from `requirements.txt`, then set your Razorpay keys.

For Windows CMD:

```bash
set RAZORPAY_KEY_ID=rzp_test_your_key_id
set RAZORPAY_KEY_SECRET=your_key_secret
python app.py
```

For Mac/Linux:

```bash
export RAZORPAY_KEY_ID=rzp_test_your_key_id
export RAZORPAY_KEY_SECRET=your_key_secret
python app.py
```

The project creates a Razorpay order on the server and verifies signature on the server.

## Project Note

The disease detection feature works immediately in image-analysis demo mode. For a complete AI/ML enhancement, follow `TRAIN_DISEASE_MODEL.md` to train a MobileNetV2 CNN model. After training, place `plant_disease_model.keras` and `class_indices.json` inside the `models` folder; `/detect` will use the trained model automatically.


## Admin Button Update

The Admin button is now placed in the top navigation bar. It has been removed from the footer quick links.

## Disease Model Training

Read `TRAIN_DISEASE_MODEL.md` for the full training workflow.
