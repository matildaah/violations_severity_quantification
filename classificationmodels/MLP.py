import pickle
import itertools
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.utils import resample
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score

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

################################ Neural Net - Multi Layer Perceptron
###### hyper parameter tuning with GridSearchCV()
## selected 10-fold cross validation
model = MLPClassifier(random_state = 44)
parameters = [{
    'hidden_layer_sizes': [(50,50,50), (50,100,50), (100,)],
    'activation': ['tanh', 'relu'],
    'solver': ['sgd', 'adam'],
    'alpha': [0.0001, 0.05],
    'learning_rate': ['constant','adaptive'],
}]


grid_mlp = GridSearchCV(model, parameters, cv=10, scoring='f1_macro')
grid_mlp.fit(trainX_upsampled, trainY_upsampled)
print(grid_mlp.best_params_)
# {'activation': 'tanh', 'alpha': 0.0001, 'hidden_layer_sizes': (50, 50, 50), 
# 'learning_rate': 'constant', 'solver': 'adam'}
print(grid_mlp.best_score_)
# 0.9125252525252525

# print prediction results
prediction = grid_mlp.predict(testX)
print(classification_report(testY, prediction))



###
df_prediction = pd.DataFrame(prediction,columns=['severity_degree'])
results = pd.concat([testX, df_prediction], axis=1)


# save model as serialized object
model = MLPClassifier(activation='tanh', hidden_layer_sizes=(50, 50, 50), alpha=0.0001, learning_rate='constant', solver='adam', random_state=44)
model.fit(trainX_upsampled, trainY_upsampled)
classifer_file = 'classification.clfser'
pickle.dump((model, trainX_upsampled, trainY_upsampled), open(classifer_file, 'wb'))



# plot confusion matrix
def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()



cnf_matrix = confusion_matrix(testY, prediction)


plt.subplot(1,2,1)
plot_confusion_matrix(cnf_matrix, classes=testY.unique(), title='MLP Classifier')
plt.show()



f1_score(testY, prediction, average=None)
# array([0.66666667, 0.84848485, 0.73684211])
f1_score(testY, prediction, average='macro')
# 0.7506645401382244
f1_score(testY, prediction, average='micro')
# 0.7674418604651162 


##### retrive most important features

results = permutation_importance(grid_mlp, testX, testY, n_repeats=30, random_state=44)
importance = results.importances_mean

df_columns = testX.columns.values.tolist()
labels=[]
perm_imp = []

# top 5 most important features
for i in results.importances_mean.argsort()[::-1]:
    if results.importances_mean[i] - 2 * results.importances_std[i] > 0:
        print(f"{df_columns[i]:<8}"
        f"{results.importances_mean[i]:.3f}"
        f" +/- {results.importances_std[i]:.3f}")
        labels.append(df_columns[i])
        perm_imp.append(results.importances_mean[i])



 # creating the bar plot
fig = plt.figure(figsize = (9, 5))
plt.bar(labels, perm_imp,
        width = 0.4, rotation=90)
plt.xlabel("Features")
plt.ylabel("Importance")
plt.title("Features importance in the MLP model")
plt.show()


