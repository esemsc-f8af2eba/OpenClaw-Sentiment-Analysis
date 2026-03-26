"""
Quick accuracy test without sklearn dependency
Uses keyword-based classification to simulate model performance
"""
import random
from collections import defaultdict

print("=" * 60)
print("  OpenClaw Model Accuracy Simulation")
print("=" * 60)

# Read data
print("\n[*] Reading data...")
with open('data/posts.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Skip header and parse
posts = []
for line in lines[1:]:
    parts = line.strip().split(',')
    if len(parts) >= 8:
        try:
            label = int(parts[-1])
            text = ','.join(parts[4:-3])  # Extract text field
            posts.append({'label': label, 'text': text})
        except:
            pass

print(f"[+] Loaded {len(posts)} posts")

# Simple keyword classifier
security_keywords = ['api', 'leak', 'rce', 'vulnerability', 'exploit',
                    'breach', 'delete', 'permission', 'hack', 'injection']
productivity_keywords = ['saves', 'time', 'automate', 'faster', 'workflow',
                        'efficient', 'streamline', 'manual', 'productivity']

def predict(text):
    text_lower = text.lower()
    security_score = sum(1 for kw in security_keywords if kw in text_lower)
    productivity_score = sum(1 for kw in productivity_keywords if kw in text_lower)

    if security_score > productivity_score:
        return 0  # Security Risk
    elif productivity_score > security_score:
        return 1  # Productivity Gain
    else:
        return 2  # Neutral

# Split and test
random.seed(42)
random.shuffle(posts)

split = int(len(posts) * 0.8)
train = posts[:split]
test = posts[split:]

print(f"[+] Train: {len(train)} | Test: {len(test)}")

# Test
correct = 0
confusion = defaultdict(lambda: defaultdict(int))

for post in test:
    true_label = post['label']
    pred_label = predict(post['text'])

    confusion[true_label][pred_label] += 1
    if true_label == pred_label:
        correct += 1

accuracy = correct / len(test)

# Results
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

label_names = {0: "Security Risk", 1: "Productivity Gain", 2: "Neutral"}

print(f"\nTest Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

print("\nConfusion Matrix:")
print("                Predicted:")
print("Actual         Security  Productivity  Neutral")
for true_label in [0, 1, 2]:
    row = [label_names[true_label][:12].ljust(12)]
    for pred_label in [0, 1, 2]:
        row.append(str(confusion[true_label][pred_label]).ljust(10))
    print("  ".join(row))

# Per-class accuracy
print("\nPer-Class Accuracy:")
for label in [0, 1, 2]:
    total = sum(confusion[label].values())
    correct_class = confusion[label][label]
    acc = correct_class / total if total > 0 else 0
    print(f"  {label_names[label]}: {acc:.2%}")

# Resume validation
print("\n" + "=" * 60)
print("RESUME CLAIM VALIDATION")
print("=" * 60)

claimed = 0.92
actual = accuracy

print(f"Claimed Accuracy: {claimed*100:.0f}%")
print(f"Actual Accuracy:  {actual*100:.2f}%")

if actual >= claimed:
    print(f"Status: PASS (exceeds claim)")
elif actual >= claimed * 0.9:
    print(f"Status: ACCEPTABLE (within 10%)")
else:
    print(f"Status: BELOW TARGET (needs improvement)")
