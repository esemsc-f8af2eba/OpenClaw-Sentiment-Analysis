"""
Helper script to save PySpark model using pickle (Windows-compatible workaround)
"""
import pickle
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import MODEL_PATH

def save_model_pickle(model, path=MODEL_PATH + ".pkl"):
    """Save model using pickle to avoid Hadoop filesystem issues on Windows"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved to {path}")
    return path

def load_model_pickle(path=MODEL_PATH + ".pkl"):
    """Load model from pickle file"""
    with open(path, "rb") as f:
        return pickle.load(f)

if __name__ == "__main__":
    print("This is a helper module. Use from train_classifier.py")
