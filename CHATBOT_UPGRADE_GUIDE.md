# Interactive Chatbot Upgrade Guide

## What has been improved

The earlier chatbot was a simple keyword-based reply system. The upgraded chatbot now works like a proper interactive plant-shop assistant.

## New chatbot features

1. Natural question handling
   - Example: `best indoor plant for bedroom`
   - Example: `plants under 300`
   - Example: `how often should I water snake plant`
   - Example: `why are my leaves turning yellow`

2. Conversation memory
   - If the user asks `how to care for snake plant` and then asks `what about watering`, the assistant remembers that the discussion is about Snake Plant.

3. Smart plant recommendations
   - Recommends plants by category, budget, difficulty, air-purifying use, gifting, indoor/outdoor need and care level.

4. Product cards inside chatbot
   - The chatbot can show plant cards with price, category, view button and add-to-cart button.

5. Voice assistant support
   - User can speak using the mic button.
   - The assistant can reply using browser speech synthesis.
   - Voice reply can be turned on or off using the speaker button.

6. Disease symptom guidance
   - Handles symptoms such as yellow leaves, brown tips, leaf spots, drooping and pests.
   - Guides the user to the Disease Check page for image upload.

7. Shopping and payment help
   - Explains cart, checkout, delivery fee and Razorpay setup.

8. Admin help
   - Explains admin login, dashboard, stock update and plant management.

## Main files changed

- `ai/chatbot.py`
- `static/js/chatbot.js`
- `static/css/style.css`
- `templates/base.html`
- `app.py`

## How the chatbot works

The chatbot works without paid external APIs. It uses:

- intent detection
- fuzzy plant name matching
- plant database search
- conversation context stored in Flask session
- frontend local chat history
- browser speech recognition
- browser speech synthesis

This is suitable for a final-year college project because it works locally and does not require paid API keys.

## How to make it more advanced later

### Option 1: Add more training data manually

Add more symptom and FAQ responses in:

```text
ai/chatbot.py
```

You can expand:

```python
SYMPTOM_KNOWLEDGE
CATEGORY_HINTS
BENEFIT_HINTS
SUGGESTION_BANK
```

### Option 2: Build an FAQ dataset

Create a CSV file like:

```text
question,intent,answer
best indoor plant,plant_recommendation,Snake Plant and Money Plant are good indoor plants.
how to water aloe vera,plant_care,Aloe Vera needs less water and bright light.
why leaves yellow,disease_help,Yellow leaves may be due to overwatering or low light.
```

Then you can train a text classification model using scikit-learn or TensorFlow.

### Option 3: Connect a real AI API

For production, you can connect an AI API and pass:

- user question
- plant database information
- cart details
- website policy

For the college demo, the current local chatbot is safer because it works without internet and gives controlled plant-shop answers.
