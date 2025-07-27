import pandas as pd
import requests
import numpy as np
import certifi
import os
import ssl
from sklearn.preprocessing import MinMaxScaler

# Create a custom SSL context
context = ssl.create_default_context()

print("Current Working Directory:", os.getcwd())
headers = {
       'Authorization': 'Bearer https://myapi.com/wallet-risk-scores'  # Replace with your actual API key
   }
# Step 1: Fetch Transaction History
def fetch_transaction_history(wallet_addresses):
    transaction_data = []
    for wallet in wallet_addresses:
        # Fetch transaction data from the API
        api_endpoint = "https://myapi.com/wallet-risk-scores"
        response = requests.get(f'{api_endpoint}/{wallet}/transactions',timeout=60, verify=certifi.where())
        
        # Check the response status code
        if response.status_code == 200:
            try:
                transactions = response.json()  # Attempt to parse JSON
                for transaction in transactions:
                    transaction_data.append({
                        'wallet_id': wallet,
                        'transaction_type': transaction['type'],
                        'value': transaction['value'],
                        'timestamp': transaction['timestamp']
                    })
            except requests.exceptions.JSONDecodeError:
                print(f"Failed to decode JSON for wallet: {wallet}")
                print(f"Response content: {response.text}")  # Print the raw response for debugging
        else:
            print(f"Failed to fetch data for wallet: {wallet}, Status Code: {response.status_code}")
            print(f"Response content: {response.text}")  # Print the raw response for debugging
        if 'application/json' in response.headers.get('Content-Type', ''):
            transactions = response.json()
        else:
            print(f"Response is not JSON for wallet: {wallet}. Response content: {response.text}")
   

    # Create DataFrame from transaction data
    transaction_df = pd.DataFrame(transaction_data)
    print("Transaction DataFrame:\n", transaction_df)  # Print the DataFrame for debugging
    return transaction_df

# Step 2: Data Preparation
def prepare_data(transaction_df):
    if 'timestamp' not in transaction_df.columns:
        print("Error: 'timestamp' column not found in transaction_df.")
        return pd.DataFrame()  # Return an empty DataFrame or handle as needed

    # Convert timestamp to datetime
    transaction_df['timestamp'] = pd.to_datetime(transaction_df['timestamp'])
    
    # Create features
    features = transaction_df.groupby('wallet_id').agg(
        total_transactions=('transaction_type', 'count'),
        total_value=('value', 'sum'),
        average_value=('value', 'mean'),
        transaction_frequency=('timestamp', lambda x: (x.max() - x.min()).days if len(x) > 1 else 0),
        last_transaction_time=('timestamp', 'max')
    ).reset_index()
    
    # Calculate time since last transaction
    features['last_transaction_time'] = (pd.Timestamp.now() - features['last_transaction_time']).dt.days
    
    return features

# The rest of your code remains unchanged...


# Step 3: Risk Scoring
def calculate_risk_score(features):
    # Normalize features
    scaler = MinMaxScaler()
    normalized_features = scaler.fit_transform(features[['total_transactions', 'total_value', 'average_value', 'transaction_frequency', 'last_transaction_time']])
    
    # Create a DataFrame for normalized features
    normalized_df = pd.DataFrame(normalized_features, columns=['total_transactions', 'total_value', 'average_value', 'transaction_frequency', 'last_transaction_time'])
    
    # Define weights for each feature (these can be adjusted based on importance)
    weights = np.array([0.25, 0.25, 0.2, 0.2, 0.1])  # Example weights
    risk_scores = normalized_df.dot(weights) * 1000  # Scale to 0-1000
    
    # Add risk scores to the features DataFrame
    features['risk_score'] = risk_scores
    return features[['wallet_id', 'risk_score']]

# Main Execution
if __name__ == "__main__":
    # Load wallet addresses from CSV
    wallet_data = pd.read_csv(r'C:\Users\KannikaHS\OneDrive\Desktop\vs code\problem statement\score\wallet_risk_scores.csv')
    wallet_addresses = wallet_data['wallet_id'].tolist()
    
    # Fetch transaction history
    transaction_df = fetch_transaction_history(wallet_addresses)
    
    # Prepare data
    features_df = prepare_data(transaction_df)
    
    # Calculate risk scores
    risk_scores_df = calculate_risk_score(features_df)
    
    # Display the risk scores
    print(risk_scores_df)
