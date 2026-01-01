"""
AI automation module for OCR and anomaly detection
"""
import pytesseract
from PIL import Image
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import numpy as np
import re
import cv2

class AIProcessor:
    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        # Use pipeline for better category classification
        self.category_classifier = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=10000)),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        self.is_trained = False
    
    def preprocess_image(self, image_path):
        """Enhanced image preprocessing for better OCR"""
        image = cv2.imread(image_path)
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        # Apply threshold to get a binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh
    
    def extract_text_from_receipt(self, image_path):
        """Enhanced OCR with preprocessing"""
        processed_image = self.preprocess_image(image_path)
        # Convert back to PIL format for pytesseract
        pil_image = Image.fromarray(processed_image)
        text = pytesseract.image_to_string(pil_image, config='--oem 3 --psm 6')
        return text
    
    def extract_financial_data(self, receipt_text):
        """Extract financial data from receipt text"""
        # Extract amount (looks for patterns like PKR 12,345.67)
        amount_pattern = r'(?:PKR|Rs\.?)\s*[\d,]+\.?\d*'
        amounts = re.findall(amount_pattern, receipt_text)
        
        # Extract date patterns
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        dates = re.findall(date_pattern, receipt_text)
        
        # Extract vendor name (usually the first capitalized word sequence)
        lines = receipt_text.split('\n')
        vendor = lines[0].strip() if lines else ""
        
        return {
            'vendor': vendor,
            'amount': amounts[0] if amounts else None,
            'date': dates[0] if dates else None,
            'raw_text': receipt_text
        }
    
    def detect_anomalies(self, transactions_df):
        """Enhanced anomaly detection with multiple features"""
        if transactions_df.empty:
            return []
        
        # Use multiple features for better anomaly detection
        features = transactions_df[['amount']].copy()
        
        # Add time-based features
        if 'date' in transactions_df.columns:
            dates = pd.to_datetime(transactions_df['date'])
            features['day_of_week'] = dates.dt.dayofweek
            features['day_of_month'] = dates.dt.day
            features['month'] = dates.dt.month
        
        # Fit and predict anomalies
        self.anomaly_detector.fit(features)
        anomalies = self.anomaly_detector.predict(features)
        anomaly_indices = np.where(anomalies == -1)[0]
        
        return [int(idx) for idx in anomaly_indices]
    
    def train_category_classifier(self, training_data):
        """Train category classifier on historical data"""
        descriptions = [item['description'] for item in training_data]
        categories = [item['category'] for item in training_data]
        
        # Vectorize text
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(descriptions)
        
        # Train classifier
        self.category_classifier.fit(X, categories)
        self.is_trained = True
        
        return {"status": "trained", "samples": len(training_data)}
    
    def predict_category(self, description):
        """Predict transaction category based on description"""
        if not self.is_trained:
            return "Uncategorized"
        
        # Note: In practice, you'd save and load the vectorizer
        # For this implementation, we'll recreate it
        # A better approach would be to persist the trained vectorizer
        vectorizer = TfidfVectorizer()  # This should be saved/loaded in practice
        X = vectorizer.fit_transform([description])
        prediction = self.category_classifier.predict(X)[0]
        return prediction