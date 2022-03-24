import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder


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

model = DummyClassifier(strategy='stratified', random_state=44)
# strategy = stratified --> based on probabilities 
model.fit(trainX, trainY)
score = model.score(testX, testY)
print(f"Model accuracy is: {score:.3f}")
# Model accuracy is: 0.442