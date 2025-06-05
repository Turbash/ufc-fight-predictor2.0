import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import joblib
import os
from ufc_scraper import config # Import config for paths

def train_models():
    print(f"Loading data from {config.LARGE_DATASET_CSV}...")
    try:
        df = pd.read_csv(config.LARGE_DATASET_CSV)
    except FileNotFoundError:
        print(f"Error: Data file not found at {config.LARGE_DATASET_CSV}")
        print("Please ensure 'large_dataset.csv' is in the 'd:\\temp\\ufc-scraper' directory.")
        return
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("Data loaded. Starting preprocessing inspired by ufc.py...")

    # 1. Drop initial columns
    df1 = df.drop(columns=['referee', 'event_name', 'r_fighter', 'b_fighter'], errors='ignore')

    # 2. Label encode all categorical (object type) columns
    # These target column names are assumed. Verify them against your CSV.
    # Common names from ufcstats.com are 'Winner' for the winner and 'finish' for the method.
    TARGET_WINNER_COL_NAME = 'winner' 
    TARGET_METHOD_COL_NAME = 'method'

    le_dict = {} 
    for col in df1.select_dtypes(include=['object']).columns:
        le = LabelEncoder()
        # Ensure NaNs are treated as a separate category if not dropped, or fill them before encoding
        df1[col] = df1[col].astype(str) # Convert to str to handle mixed types/NaNs uniformly before encoding
        df1[col] = le.fit_transform(df1[col])
        le_dict[col] = le
        # If you want to see the mapping for target columns:
        if col == TARGET_WINNER_COL_NAME or col == TARGET_METHOD_COL_NAME:
            print(f"LabelEncoder mapping for column '{col}':")
            try:
                # Show mapping for up to 10 classes to avoid overly long prints
                classes_to_show = le.classes_[:10]
                for i, class_label in enumerate(classes_to_show):
                    print(f"  '{class_label}' -> {le.transform([class_label])[0]}")
                if len(le.classes_) > 10:
                    print(f"  ... and {len(le.classes_) - 10} more classes.")
            except Exception as e_le:
                print(f"Could not display LabelEncoder classes for {col}: {e_le}")


    print("Label encoding completed.")
    
    # Verify target columns exist after potential initial drops and before general dropna
    if TARGET_WINNER_COL_NAME not in df1.columns:
        print(f"Error: Crucial target column '{TARGET_WINNER_COL_NAME}' not found in DataFrame columns: {list(df1.columns[:15])}. Please check CSV header or TARGET_WINNER_COL_NAME.")
        return
    if TARGET_METHOD_COL_NAME not in df1.columns:
        print(f"Error: Crucial target column '{TARGET_METHOD_COL_NAME}' not found in DataFrame columns: {list(df1.columns[:15])}. Please check CSV header or TARGET_METHOD_COL_NAME.")
        return

    # 3. Perform dropna() on the entire dataframe (mirrors notebook's pdf1.dropna())
    # This df_cleaned_all will be the basis for X and y.
    # It now contains integer-encoded target columns (if they were objects).
    df_cleaned_all = df1.dropna()
    print(f"Shape after dropping all NaNs (from df1): {df_cleaned_all.shape}")

    if df_cleaned_all.empty:
        print("DataFrame is empty after dropping NaNs from df1. Cannot proceed with training.")
        return

    # 4. Define targets y_winner and y_method FROM df_cleaned_all
    # These columns should now be integer-encoded.
    if TARGET_WINNER_COL_NAME not in df_cleaned_all.columns:
        print(f"Error: Target column '{TARGET_WINNER_COL_NAME}' is not in df_cleaned_all columns after dropna. This should not happen if it was in df1.")
        return
    if TARGET_METHOD_COL_NAME not in df_cleaned_all.columns:
        print(f"Error: Target column '{TARGET_METHOD_COL_NAME}' is not in df_cleaned_all columns after dropna.")
        return
        
    y_winner = df_cleaned_all[TARGET_WINNER_COL_NAME]
    y_method = df_cleaned_all[TARGET_METHOD_COL_NAME]

    # 5. Define features X by dropping target-related and other specified columns FROM df_cleaned_all
    # Columns to drop for features, based on notebook's pdf2=pdf1.drop(columns=['method','finish_round','time_sec','winner'])
    # Using our defined target column names.
    cols_to_drop_for_features = [TARGET_METHOD_COL_NAME, 'finish_round', 'time_sec', TARGET_WINNER_COL_NAME]
    # Ensure these columns actually exist in df_cleaned_all before trying to drop for X
    actual_cols_to_drop_for_X = [col for col in cols_to_drop_for_features if col in df_cleaned_all.columns]
    
    X = df_cleaned_all.drop(columns=actual_cols_to_drop_for_X)
    print(f"Shape of X before final feature cleaning (dropna on X): {X.shape}")

    # 6. Clean NaNs from the feature set X (mirrors notebook's pdf3=pdf2.dropna())
    X_final = X.dropna()
    print(f"Shape of X_final after its own dropna: {X_final.shape}")

    if X_final.empty:
        print("Feature set X_final is empty after its own dropna. Cannot train models.")
        return
        
    # 7. Align y targets with the cleaned X_final's index
    y_winner_final = y_winner.loc[X_final.index]
    y_method_final = y_method.loc[X_final.index]
    print(f"Shapes after aligning with X_final: y_winner_final: {y_winner_final.shape}, y_method_final: {y_method_final.shape}")

    # Print distribution of encoded target values to help with app.py maps
    print("\nEncoded Winner Target (y_winner_final) Info (value -> count):")
    print(y_winner_final.value_counts(dropna=False).to_dict())
    
    print("\nEncoded Method Target (y_method_final) Info (value -> count):")
    print(y_method_final.value_counts(dropna=False).to_dict())


    # 8. Save feature names
    feature_names = list(X_final.columns)
    joblib.dump(feature_names, config.MODELS_DIR / 'feature_names.pkl')
    print(f"Feature names saved. Total features: {len(feature_names)}")

    # --- Train Winner Prediction Model (XGBoost) ---
    print("\nTraining Winner Prediction Model (XGBoost)...")
    if len(y_winner_final.unique()) < 2:
        print("Winner target has less than 2 unique values. Skipping winner model training.")
    else:
        X_train_w, X_test_w, y_train_w, y_test_w = train_test_split(X_final, y_winner_final, test_size=0.2, random_state=42, stratify=y_winner_final)
        model_winner = xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss')
        model_winner.fit(X_train_w, y_train_w)
        print(f"Winner model accuracy: {model_winner.score(X_test_w, y_test_w):.4f}")
        joblib.dump(model_winner, config.MODELS_DIR / 'xgboost_fight_winner.pkl')
        print(f"Winner prediction model saved to {config.MODELS_DIR / 'xgboost_fight_winner.pkl'}")

    # --- Train Finish Prediction Model (XGBoost) ---
    print("\nTraining Finish Prediction Model (XGBoost)...")
    num_classes_method = len(y_method_final.unique())
    if num_classes_method < 2:
        print("Method target has less than 2 unique classes. Skipping method model training.")
    else:
        X_train_f, X_test_f, y_train_f, y_test_f = train_test_split(X_final, y_method_final, test_size=0.2, random_state=42, stratify=y_method_final)
        model_finish = xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='mlogloss', objective='multi:softmax', num_class=num_classes_method)
        model_finish.fit(X_train_f, y_train_f)
        print(f"Finish model accuracy: {model_finish.score(X_test_f, y_test_f):.4f}")
        joblib.dump(model_finish, config.MODELS_DIR / 'xgboost_finish_prediction.pkl')
        print(f"Finish prediction model saved to {config.MODELS_DIR / 'xgboost_finish_prediction.pkl'}")

    print("\nModel training process completed.")

if __name__ == '__main__':
    train_models()
