import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score

class UserPredictor(BaseEstimator):
    def __init__(self):
        # Initialize the pipeline
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression())
        ])
        self.xcols = None  # Placeholder for feature columns names

    def fit(self, train_users, train_logs, train_y):
        # Prepare the training data by merging and feature engineering
        train_df = self.prepare_features(train_users, train_logs)
        self.xcols = [col for col in train_df.columns if col != 'id' and col != 'clicked']
        
        # Fit the model
        self.pipeline.fit(train_df[self.xcols], train_y['clicked'])
        
        # Optional: cross-validation to check for stability of model
        scores = cross_val_score(self.pipeline, train_df[self.xcols], train_y['clicked'], cv=5)
        print(f"AVG: {scores.mean()}, STD: {scores.std()}\n")

    def predict(self, test_users, test_logs):
        # Prepare the test data like the training data
        test_df = self.prepare_features(test_users, test_logs)
        
        # Predict using the pipeline
        return self.pipeline.predict(test_df[self.xcols])

    def prepare_features(self, users_df, logs_df):
        # Handling categorical variables by one-hot encoding
        users_df = pd.get_dummies(users_df, columns=['badge'], drop_first=True)
    
        # Aggregate logs data
        logs_agg = logs_df.groupby('id').agg(total_duration=('duration', 'sum')).reset_index()
        
        # Merge users and logs dataframes on 'id'
        merged_df = pd.merge(users_df, logs_agg, on='id', how='left')
    
        # Handling possible missing values in logs data
        merged_df['total_duration'].fillna(0, inplace=True)
    
        # Remove non-numeric columns like 'name'
        merged_df.drop(columns=['name'], inplace=True)
        
        return merged_df

# Example of usage
if __name__ == "__main__":
    model = UserPredictor()
    train_users = pd.read_csv("data/train_users.csv")
    train_logs = pd.read_csv("data/train_logs.csv")
    train_y = pd.read_csv("data/train_clicked.csv")

    model.fit(train_users, train_logs, train_y)

    test_users = pd.read_csv("data/test1_users.csv")
    test_logs = pd.read_csv("data/test1_logs.csv")
    y_pred = model.predict(test_users, test_logs)
