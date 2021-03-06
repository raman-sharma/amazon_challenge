import numpy as np
import scipy as sp
import sklearn.linear_model as lm
from sklearn.ensemble import RandomTreesEmbedding,RandomForestClassifier,GradientBoostingClassifier,AdaBoostClassifier,ExtraTreesClassifier
from sklearn import metrics,preprocessing,cross_validation
from sklearn.lda import LDA
import utils
import SMOTE
import ADASYN

loadData = lambda f: np.genfromtxt(open(f,'r'), delimiter=',')

amazon_new = loadData('../data/train_orig.csv')
labels = amazon_new[1:,0]
traindata = amazon_new[1:,1:] # 1-> 2

orig_lbl = labels
orig_lbl = np.reshape(orig_lbl,(-1,1))

print "importing from dump!"
orig_test = np.load('../data/X_test_all.dat')
orig_train= np.load('../data/X_train_all.dat')
num_features = orig_train.shape[1]
num_train = orig_train.shape[0]
ortrain = orig_train
ortest = orig_test
print "import done.."

traindata = orig_train
testdata = orig_test

print "training size:", traindata.shape
print "test data size:", testdata.shape

print "select good features..."
orig_good =   [0, 12, 15, 29, 44, 52, 65, 75, 83, 92, 94, 110, 115, 165, 170, 195, 202, 267, 272, 278, 323, 374, 405, 406, 407, 462, 473, 497, 524, 527, 528, 536, 539]
Xt = np.vstack((traindata,testdata))
Xt = Xt[:,orig_good]


print "perform one hot encoding .."
#Xt, keymap = utils.OneHotEncoder(Xt)
traindata = Xt[:num_train]
testdata = Xt[num_train:]

classifier1 = lm.SGDClassifier(loss='log', penalty='l2', alpha=0.0001, 
                              l1_ratio=.14999999999999999, fit_intercept=True, n_iter=5000, shuffle=False, 
                              verbose=0, epsilon=0.10000000000000001, n_jobs=-1, 
                              random_state=None, learning_rate='optimal', eta0=0.0, power_t=0.5, 
                              class_weight=None, warm_start=False, rho=None, seed=None)

classifier2 = RandomForestClassifier(n_estimators=50, criterion='gini', max_depth=20, 
                               min_samples_split=3, min_samples_leaf=25, min_density=0.0000000000000001, max_features="auto", bootstrap=True,
                               oob_score=True, n_jobs=-1,
                               random_state=None, verbose=1)

classifier3 = lm.LogisticRegression(C = 1.54)
classifier4 = LDA()

print "Cross Validation"
X = traindata
y = labels
mean_auc = 0.0
n = 10  # repeat the CV procedure 10 times to get more precise results
#===============================================================================
for i in range(n):
    print "======================================= CROSS VALIDATION LOOP: ", (i+1)

    # for each iteration, randomly hold out 20% of the data as CV set
    X_train, X_cv, y_train, y_cv = cross_validation.train_test_split(
        X, y, test_size=.20, random_state=i*25)

    print "training size: ", X_train.shape
    print "label size: ", y_train.shape 
    
    print "the ADASYN goodie..."

    y_train = list(np.array(y_train).reshape(-1,))
    ms,ml = ADASYN.getClassCount(X_train,y_train)
    print ms, ml

    d = ADASYN.getd(X_train,y_train,ms,ml)
    G = ADASYN.getG(X_train,y_train,ms,ml,1)

    # Get the list of r values, which indicate how many samples will be made per data point in the minority dataset
    rlist = ADASYN.getRis(X_train,y_train,0,2)

    # Generate the synthetic data
    newX,newy = ADASYN.generateSamples(rlist,X_train,y_train,G,0,2)
    
    X_train,y_train = ADASYN.joinwithmajorityClass(X_train,y_train,newX,newy,1)

    print "new training size: ", X_train.shape
    print "new label size: ", y_train.shape 

    
    
    print "perform one hot encoding .."
    num_train = X_train.shape[0]
    Xt = np.vstack((X_train,X_cv))
    Xt, keymap = utils.OneHotEncoder(Xt)
    X_train = Xt[:num_train]
    X_cv = Xt[num_train:]

    classifier3.fit(X_train, y_train)
    preds1 = classifier3.predict_proba(X_cv)[:,1]

    fpr, tpr, thresholds = metrics.roc_curve(y_cv, preds1)
    roc_auc = metrics.auc(fpr, tpr)
    print "AUC (fold %d/%d): %f" % (i + 1, n, roc_auc)
    #print roc_auc
    mean_auc += roc_auc
  
print "Mean AUC: %f" % (mean_auc/n)
#===============================================================================