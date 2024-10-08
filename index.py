import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from fpdf import FPDF



def detect_malware_in_file(file_path, threshlod = 35):

    try:

        data = pd.read_csv(file_path)

        if 'hash' not in data.columns:

            raise ValueError("The file does not contain a 'hash' column ")
        
        data['hash_lenght'] = data['hash'].apply(len)

        data['classification'] = data['hash_lenght'].apply(lambda x: 1 if x > threshlod else 0)

        print("\nHash and Classification based on hash lenght: ")
        print(data[['hash', 'hash_lenght', 'classification']])

       
        print(f"\nTotal Malware: {(data['classification'] == 1).sum()}")
        print(f"\nTotal Benign: {(data['classification'] == 0).sum()}")

        return data
    
    except Exception as e:

        print(f"Error processing the file: {e}")

file_path = input("Please enter the path to your CSV file: ")

data = detect_malware_in_file(file_path, threshlod=35)


def extract_hash_features(hash_value):
    hash_lenght = len(hash_value)
    numeric_value = sum(c.isdigit() for c in hash_value)
    alphabetic_count = sum(c.isalpha() for c in hash_value)
    special_char_count = sum(not c.isalnum() for c in hash_value)

    return pd.Series([hash_lenght, numeric_value, alphabetic_count, special_char_count])


if data is not None :

    hash_features = data['hash'].apply(extract_hash_features)
    hash_features = pd.DataFrame(hash_features.values.tolist(), columns=['hash_lenght', 'numeric_count', 'alphabetic_count', 'special_char_count'])
    
    data = data.drop(columns=['hash'])
    data = pd.concat([data, hash_features], axis=1)

    data['classification'] = data['classification'].map({1:1, 0:0}) 


    print("\nChecking for missing values:")
    print(data.isnull().sum())


    X = data.drop(columns=['classification']) 
    y = data['classification'] 


    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)


    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, stratify=y, random_state=42)

    if len(set(y_train)) < 1:
        print("Training data must contain at least two classes for RandomForest")
        exit()

    model = RandomForestClassifier(random_state=42)


    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
    print(f"\nCross-Validation Scores: {cv_scores}")
    print(f"Mean Accuracy: {cv_scores.mean():.2f}")


    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [10, 20, 30, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    grid_search = GridSearchCV(model, param_grid, cv=5, scoring='accuracy', n_jobs=-1)
    grid_search.fit(X_train, y_train)
    best_params = grid_search.best_params_
    print(f"\nBest Hyperparameters: {best_params}")


    model = RandomForestClassifier(**best_params, random_state=42)
    model.fit(X_train, y_train)


    print("\nMaking predictions on the test data...")
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy * 100:.2f}%")


    print("y_test:", y_test[: 10])
    print("y_pred:", y_pred[: 10])
    print("\nY_test distribution:\n", pd.Series(y_test).value_counts())
    print("Y_pred distribution:\n", pd.Series(y_pred).value_counts())


    if len(pd.Series(y_test).unique()) == 0:
        print("Skipping Classification Report as only one class is present in y_test.")
        classification_rep = "Not generated due to a single class in y_test."
    else:
        classification_rep = classification_report(y_test, y_pred, labels=[0, 1])
        print("\nClassification Report:")
        print(classification_rep)


    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Benign', 'Malware'], yticklabels=['Benign', 'Malware'])
    plt.title('Confusion Matrix')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.show()


    try:
        roc_auc = roc_auc_score(y_test, y_pred)
        print(f"\nROC-AUC Score: {roc_auc:.2f}")
    except ValueError as e:
        print(f"ROC-AUC Score could not be calculated: {e}")
        roc_auc = None  


    feature_importances = pd.Series(model.feature_importances_, index=X.columns)
    plt.figure(figsize=(10, 6))
    sns.barplot(x=feature_importances, y=feature_importances.index)
    plt.title('Feature Importance')
    plt.xlabel('Importance')
    plt.ylabel('Features')
    plt.tight_layout()
    plt.show()


    joblib.dump(model, 'malware_model.pkl')
    print("\nModel saved as 'malware_model.pkl'")


    def generate_pdf_report(accuracy, classification_rep, roc_auc, feature_importances):
        plt.figure(figsize=(8,6))
        sns.heatmap(cm, annot=True,fmt='d',cmap='Blues',xticklabels=['Benign','Malware'], yticklabels=['Benign', 'Malware'])
        plt.title('Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.tight_layout()
        plt.savefig('confusion_matrix.png')
        plt.close()
    
    #-------------------------------------------

        plt.figure(figsize=(10,6))
        sns.barplot(x=feature_importances, y=feature_importances.index)
        plt.xlabel('Importance')
        plt.ylabel('Features')
        plt.savefig('feature_importance.png')
        plt.close()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(200, 10, txt="Malware Analysis Report", ln=True, align='C')
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(200, 10, txt=f"Model Accuracy: {accuracy * 100:.2f}%", ln=True)
        if roc_auc is not None:
            pdf.cell(200, 10, txt=f"ROC-AUC Score: {roc_auc:.2f}", ln=True)
        else:
            pdf.cell(200,10,txt="ROC-AUC Score: Not Applicable", ln=True)
        pdf.cell(200, 10, txt="Classification Report:", ln=True)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 10, classification_rep)
    
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(200, 10, txt="Confusion Matrix:", ln=True)
        pdf.image('confusion_matrix.png', x=10, y=None,w=100)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(200, 10, txt="Feature Importances:", ln=True)
        pdf.image('feature_importance.png', x=10, y=None,w=100)

        pdf.set_font('Arial', '', 10)
        for feature, importance in feature_importances.items():
            pdf.cell(200, 10, txt=f"{feature}: {importance:.4f}", ln=True)
        pdf.output('Malware_Analysis_Report.pdf')
        print("\nPDF report generated as 'Malware_Analysis_Report.pdf'")
    def generate_csv_report(y_test, y_pred):
        report_df = pd.DataFrame({
            'Actual': y_test,
            'Predicted': y_pred
        })
        report_df.to_csv('Malware_Analysis_Report.csv', index=False)
        print("\nCSV report generated as 'Malware_Analysis_Report.csv'")


    generate_pdf_report(accuracy, classification_rep, roc_auc, feature_importances)
    generate_csv_report(y_test, y_pred)
