# Setup Guide - Akshaya AI Plant Shop

## 1. Open Project in VS Code

Open the folder `Akshaya_AI_Plant_Shop_Professional` in VS Code.

## 2. Create Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Required Packages

```bash
pip install -r requirements.txt
```

## 4. Run Website

```bash
python app.py
```

Open in browser:

```text
http://127.0.0.1:5000
```

## 5. Admin Login

Open:

```text
http://127.0.0.1:5000/admin/login
```

Default login:

```text
Username: admin
Password: admin123
```

## 6. How to Add More Plants

1. Login to admin panel.
2. Click `Add New Plant`.
3. Fill plant name, category, price, stock, sunlight, water, soil, fertilizer, benefits and description.
4. Save.

## 7. How Chatbot Works

The chatbot is available as a floating button on all pages. It answers questions about:

- Watering
- Sunlight
- Soil
- Fertilizer
- Beginner plants
- Air-purifying plants
- Cart and payment help
- Disease care suggestions

## 8. How Voice Assistant Works

The voice assistant uses browser Web Speech API. It works best in Google Chrome.

Steps:

1. Click the chat icon.
2. Click the mic button.
3. Speak your plant-related question.
4. The chatbot will reply and speak the answer.

## 9. Razorpay Payment Setup

The project already contains payment-ready backend routes:

- `/api/payment/create-razorpay-order`
- `/api/payment/verify`

Set your test keys before running:

Windows CMD:

```bash
set RAZORPAY_KEY_ID=rzp_test_your_key_id
set RAZORPAY_KEY_SECRET=your_key_secret
python app.py
```

Mac/Linux:

```bash
export RAZORPAY_KEY_ID=rzp_test_your_key_id
export RAZORPAY_KEY_SECRET=your_key_secret
python app.py
```

## 10. Important Project Explanation

For college project demo, Cash on Delivery works immediately. Razorpay needs real test keys from Razorpay Dashboard. Disease detection now works in image-analysis demo mode. For a pure AI/ML enhancement, train the CNN model using the instructions in `TRAIN_DISEASE_MODEL.md`. After training, save the model files in the `models` folder and the `/detect` route will automatically use the trained model.


## 11. Disease Check Fix

The disease page now previews the uploaded image, handles errors clearly, and checks the uploaded image using the backend. It no longer depends only on the file name.

## 12. Admin Button Placement

The Admin button is now available at the top navigation bar. After login, it changes to Admin Dashboard and Logout.
