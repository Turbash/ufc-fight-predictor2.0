from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import xgboost # Ensure xgboost is imported
import os
from typing import List, Dict, Any
from ufc_scraper import config # Import config for paths

app = FastAPI(
    title="UFC Fight Predictor API",
    description="API to predict UFC fight outcomes and finish methods using XGBoost models.",
    version="1.0.0"
)

# --- Pydantic Models ---
class PredictionRequest(BaseModel):
    r_fighter_name: str = Field(..., example="Amanda Ribas")
    b_fighter_name: str = Field(..., example="Rose Namajunas")
    # The example features list needs to match the actual number of features from your trained model
    # This will be determined by feature_names.pkl after running model_trainer.py
    features: List[float] = Field(..., example=[0.5] * 50) # Placeholder, adjust length after training

class PredictionResponse(BaseModel):
    r_fighter_name: str
    b_fighter_name: str
    predicted_winner: str
    winner_determination_class: str # e.g., "Red" or "Blue" (or original encoded values)
    confidence: float
    finish_prediction: str # e.g., "KO/TKO", "Submission" (or original encoded values)
    note: str

# --- Globals for Models and Config ---
model_fight_winner = None
model_finish_prediction = None
feature_names = []

# Mappings: These need to align with how LabelEncoder in model_trainer.py encodes 'Winner' and 'finish'
# You'll need to inspect the saved LabelEncoder or the unique values in y_winner/y_method
# For example, if LabelEncoder maps 'Red' to 0 and 'Blue' to 1 for winner:
winner_class_map: Dict[int, str] = {0: "Red", 1: "Blue"} # Example: Update based on actual encoding
# For finish, if 'KO/TKO' is 0, 'SUB' is 1, 'U-DEC' is 2 etc.
finish_map: Dict[int, str] = { 
    0: "KO/TKO", 1: "Submission", 2: "Decision - Unanimous", 
    3: "Decision - Split", 4: "Decision - Majority", 5: "DQ" # Example: Update based on actual encoding
} 
# It's crucial these maps correctly interpret the numeric output of your models.

# --- Model Loading ---
@app.on_event("startup")
async def load_application_models():
    global model_fight_winner, model_finish_prediction, feature_names
    
    model_winner_path = config.MODELS_DIR / 'xgboost_fight_winner.pkl'
    model_finish_path = config.MODELS_DIR / 'xgboost_finish_prediction.pkl'
    feature_names_path = config.MODELS_DIR / 'feature_names.pkl'

    try:
        model_fight_winner = joblib.load(model_winner_path)
        print(f"Fight winner model loaded successfully from {model_winner_path}.")
    except FileNotFoundError:
        print(f"Warning: Fight winner model file not found at {model_winner_path}.")
    except Exception as e:
        print(f"Error loading fight winner model: {e}")

    try:
        model_finish_prediction = joblib.load(model_finish_path)
        print(f"Finish prediction model loaded successfully from {model_finish_path}.")
    except FileNotFoundError:
        print(f"Warning: Finish prediction model file not found at {model_finish_path}.")
    except Exception as e:
        print(f"Error loading finish prediction model: {e}")

    try:
        feature_names = joblib.load(feature_names_path)
        print(f"Feature names loaded successfully from {feature_names_path}. Expecting {len(feature_names)} features.")
    except FileNotFoundError:
        print(f"CRITICAL: feature_names.pkl not found at {feature_names_path}. Predictions will fail.")
        feature_names = [] 
    except Exception as e:
        print(f"Error loading feature names: {e}")
        feature_names = []

    if not model_fight_winner or not model_finish_prediction or not feature_names:
        print("CRITICAL: One or more models or feature names failed to load. API might not function correctly.")
    else:
        print("All models and feature names loaded successfully.")

# --- Prediction Endpoint ---
@app.post("/predict", response_model=PredictionResponse)
async def predict(request_data: PredictionRequest):
    if not model_fight_winner or not model_finish_prediction:
        raise HTTPException(status_code=503, detail={
            "error": "Models not loaded.",
            "note": f"Ensure model files are in {config.MODELS_DIR}"
        })
    
    if not feature_names:
        raise HTTPException(status_code=503, detail="Feature names configuration is missing. Cannot make predictions.")

    if len(request_data.features) != len(feature_names):
        raise HTTPException(status_code=400, detail=f"Feature mismatch. Expected {len(feature_names)} features, got {len(request_data.features)}.")

    try:
        input_df = pd.DataFrame([request_data.features], columns=feature_names)

        # Winner prediction
        winner_pred_proba = model_fight_winner.predict_proba(input_df)[0]
        winner_pred_class = int(model_fight_winner.predict(input_df)[0]) 
        
        # Map numeric prediction to fighter name
        # This assumes winner_class_map keys (0, 1) correspond to 'Red', 'Blue'
        # And your model's output for winner aligns with this.
        predicted_winner_label = winner_class_map.get(winner_pred_class, f"Unknown Class {winner_pred_class}")
        if predicted_winner_label == "Red": # Or however your 'Winner' column was encoded for class 0
            predicted_winner_name = request_data.r_fighter_name
        elif predicted_winner_label == "Blue": # Or however your 'Winner' column was encoded for class 1
            predicted_winner_name = request_data.b_fighter_name
        else:
            predicted_winner_name = predicted_winner_label # e.g. "Unknown Class X"

        confidence = float(winner_pred_proba[winner_pred_class])

        # Finish prediction
        finish_pred_class = int(model_finish_prediction.predict(input_df)[0])
        predicted_finish_method = finish_map.get(finish_pred_class, f"Unknown Finish Method (Class {finish_pred_class})")

        return PredictionResponse(
            r_fighter_name=request_data.r_fighter_name,
            b_fighter_name=request_data.b_fighter_name,
            predicted_winner=predicted_winner_name,
            winner_determination_class=predicted_winner_label,
            confidence=round(confidence, 4),
            finish_prediction=predicted_finish_method,
            note="Predictions based on XGBoost models."
        )

    except AttributeError as ae:
        print(f"Error during prediction - model interface issue: {ae}")
        raise HTTPException(status_code=500, detail="Prediction failed due to a model interface error.")
    except Exception as e:
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed due to an internal error.")

# --- Main execution for Uvicorn ---
if __name__ == "__main__":
    import uvicorn
    # config.py already creates MODELS_DIR on import
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
