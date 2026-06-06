"""Feature engineering — digunakan oleh training dan FastAPI."""

import joblib, os

FEATURE_COLUMNS = [
    'brand_enc', 'model_enc', 'motor_age', 'mileage_km',
    'condition_engine', 'condition_body',
    'has_complete_docs', 'has_service_history', 'has_modification',
    'city_enc',
]

ENCODER_PATH = os.path.join(os.path.dirname(__file__), 'encoders.pkl')


def create_encoders(df):
    from sklearn.preprocessing import LabelEncoder
    encoders = {}
    for col in ['brand', 'model', 'location_city']:
        le = LabelEncoder()
        le.fit(df[col].fillna('unknown'))
        encoders[col] = le
    return encoders


def save_encoders(encoders):
    joblib.dump(encoders, ENCODER_PATH)


def load_encoders():
    return joblib.load(ENCODER_PATH)


def engineer_features_training(df, encoders):
    df = df.copy()
    df['mileage_km']    = df['mileage_km'].fillna(df['mileage_km'].median())
    df['location_city'] = df['location_city'].fillna('unknown')
    df['motor_age']     = 2026 - df['year']
    df['brand_enc']     = encoders['brand'].transform(df['brand'].fillna('unknown'))
    df['model_enc']     = encoders['model'].transform(df['model'].fillna('unknown'))
    df['city_enc']      = encoders['location_city'].transform(df['location_city'].fillna('unknown'))
    return df[FEATURE_COLUMNS]


def engineer_features_prediction(input_dict, encoders):
    def safe_encode(enc, val):
        try:
            return int(enc.transform([val])[0])
        except ValueError:
            return 0

    return [
        safe_encode(encoders['brand'], input_dict['brand']),
        safe_encode(encoders['model'], input_dict['model']),
        2026 - input_dict['year'],
        input_dict['mileage_km'],
        input_dict['condition_engine'],
        input_dict['condition_body'],
        int(input_dict['has_complete_docs']),
        int(input_dict['has_service_history']),
        int(input_dict['has_modification']),
        0,  # city default
    ]