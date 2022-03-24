import pandas as pd
import statistics
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.utils import resample
from sklearn.metrics import classification_report

# TODO add dir of violations file
################# dataset load
excel_file = 'filtered_violations_dataset.xlsx'
df = pd.read_excel(excel_file)
df.head()

##### label encoding
# vaa type: VA, BVA, NVA
encoder1 = OneHotEncoder()
encoder_vaa_type = encoder1.fit_transform(df[["vaa_type"]])
pd.DataFrame(encoder_vaa_type.toarray(), columns=encoder1.categories_).head()
df = df.join(pd.DataFrame(encoder_vaa_type.toarray(), columns=encoder1.get_feature_names(['vaa_type'])))

# violation type = skip, add
encoder2 = OneHotEncoder()
encoder_violation_type = encoder2.fit_transform(df[["violation_type"]])
pd.DataFrame(encoder_violation_type.toarray(), columns=encoder2.categories_).head()
df = df.join(pd.DataFrame(encoder_violation_type.toarray(), columns=encoder2.get_feature_names(['violation_type'])))

# activity position: start, end, core
encoder3 = OneHotEncoder()
encoder_activity_pos = encoder3.fit_transform(df[["activity_position"]])
pd.DataFrame(encoder_activity_pos.toarray(), columns=encoder3.categories_).head()
df = df.join(pd.DataFrame(encoder_activity_pos.toarray(), columns=encoder3.get_feature_names(['activity_position'])))

# decision activity: True, False
encoder4 = OneHotEncoder()
encoder_decision_act = encoder4.fit_transform(df[["decision_activity"]])
pd.DataFrame(encoder_decision_act.toarray(), columns=encoder4.categories_).head()
df = df.join(pd.DataFrame(encoder_decision_act.toarray(), columns=encoder4.get_feature_names(['decision_activity'])))

## remove non relevant attributes
df = df.drop(columns=['event', 'preprocessed event', 'matched_vaa_activity', 'vaa_type', 'violation_type','activity_position','decision_activity'], axis=1)
df.head()


##############
# data split 
y = df['severity_degree']
x = df.drop('severity_degree', axis=1)

trainX, testX, trainY, testY = train_test_split(x, y, test_size=0.3, random_state = 44)
#display(testY)  

# create training dataframe & upsampling minority classes
df_training =  pd.concat([trainX, trainY], axis=1)
df_training.head()

df_training['severity_degree'].value_counts()
# L 36 | M 42 | H 20

# part 1: upsample 'high' class
high_category = df_training[df_training["severity_degree"] == "H"]
other_categories = df_training[df_training["severity_degree"] != "H"]

high_upsample = resample(high_category,
             replace=True,
             n_samples=42,
             random_state=44)
data_upsampled = pd.concat([other_categories, high_upsample])
print(data_upsampled.shape)
data_upsampled.head()

# part 2: upsample 'low' class 
low_category = data_upsampled[data_upsampled["severity_degree"] == "L"]
other_categores = data_upsampled[data_upsampled["severity_degree"] != "L"]
low_upsample = resample(low_category,
             replace=True,
             n_samples=42,
             random_state=44)
data_upsampled2 = pd.concat([other_categores, low_upsample])
print(data_upsampled2.shape)
data_upsampled2.head()

data_upsampled2['severity_degree'].value_counts()
# L 42 | M  42 | H 42 


trainY_upsampled = data_upsampled['severity_degree']
trainX_upsampled = data_upsampled.drop('severity_degree', axis=1)


############################### Ensembles - Random Forest Classifier
####### hyperparameter tuning with 10-fold cross validation
model = RandomForestClassifier(random_state = 44)
parameters = [{
    'min_samples_split': [8, 10, 12],
    'n_estimators': [100, 200, 300, 1000]
}]

grid_rfc = GridSearchCV(model, parameters, cv=10, scoring='f1_macro')
grid_rfc.fit(trainX_upsampled, trainY_upsampled)
print(grid_rfc.best_params_)
# {'min_samples_split': 8, 'n_estimators': 300}
print(grid_rfc.best_score_)
# 0.8119793169793169

# print prediction results
prediction = grid_rfc.predict(testX)
print(classification_report(testY, prediction))

#####################################
df_prediction = pd.DataFrame(prediction,columns=['severity_degree'])
results = pd.concat([testX, df_prediction], axis=1)

