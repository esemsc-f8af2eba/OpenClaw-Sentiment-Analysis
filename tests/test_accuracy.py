"""
Test Model Accuracy using scikit-learn
Verifies the 92% accuracy claim
"""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("=" * 60)
print("  Model Accuracy Test (scikit-learn)")
print("=" * 60)

# Load data
print("\n[*] Loading data...")
df = pd.read_csv('data/posts.csv')
print(f"[+] Loaded {len(df)} posts")

# Check label distribution
print("\n[*] Label distribution:")
print(df['label'].value_counts().sort_index())

# Prepare features
print("\n[*] Preparing features...")
X = df['text'].fillna('')
y = df['label']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"[+] Train: {len(X_train)} | Test: {len(X_test)}")

# Create TF-IDF features
print("\n[*] Creating TF-IDF features...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    stop_words='english',
    ngram_range=(1, 2)
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Train model
print("\n[*] Training Logistic Regression...")
model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train_tfidf, y_train)

# Predict
y_pred = model.predict(X_test_tfidf)

# Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"\nTest Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"\nPer-Class Report:")
print(classification_report(y_test, y_pred,
                          target_names=['Security Risk', 'Productivity Gain', 'Neutral']))

# Resume validation
print("\n" + "=" * 60)
print("RESUME CLAIM VALIDATION")
print("=" * 60)

if accuracy >= 0.92:
    status = "PASS"
elif accuracy >= 0.85:
    status = "ACCEPTABLE"
else:
    status = "BELOW TARGET"

print(f"Claimed Accuracy: 92%")
print(f"Actual Accuracy: {accuracy*100:.2f}%")
print(f"Status: {status}")

# Show some predictions
print("\n" + "=" * 60)
print("Sample Predictions")
print("=" * 60)

label_names = {0: "Security Risk", 1: "Productivity Gain", 2: "Neutral"}
sample_texts = [
    "OpenClaw exposed my API key in logs",
    "This tool saves me hours every day",
    "Anyone know how to configure OpenClaw?"
]

print("\nTest predictions:")
for text in sample_texts:
    text_tfidf = vectorizer.transform([text])
    pred = model.predict(text_tfidf)[0]
    proba = model.predict_proba(text_tfidf)[0]
    print(f"  Text: '{text}'")
    print(f"  → Predicted: {label_names[pred]} (confidence: {proba[pred]:.2%})")
