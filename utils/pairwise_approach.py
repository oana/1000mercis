import numpy as np
from sklearn import svm
import copy

def transform_pairwise(X, Y):
    """
    Transforms data into pairs with balanced labels for ranking
    Transforms a n-class ranking problem into a two-class classification
    problem.
    In this method, all pairs are chosen, except for those that have the
    same target value. The output is an array of balanced classes, i.e.
    there are the same number of -1 as +1
    
    Parameters
    ----------
    X : array, shape (n_samples, n_features)
        The data
    Y : array, shape (n_samples, 2)
        Target labels. The second column represents the grouping of samples,
        i.e., samples with different groups will not be considered.
        
    Returns
    -------
    X_trans : array, shape (k, n_features)
        Data as pairs
    Y_trans : array, shape (k,)
        Output class labels, where classes have values {-1, +1}
    Z_trans : array, shape (k,)
        Output id for each pair
    """


    #X the data

    #Y(:,0) : Rank
    #Y(:,1) : user_id

    #Initiate the output
    X_new = []
    Y_new = []
    Z_new = []
    
    Y = np.asarray(Y)
    
    current_id = -1
    i = 0
    k = 0
    rank1 = []
    rank2 = []
    #sumId = []
    
    #For each sample, we check its id
    while i < len(X):
        # If its id is matching the id we are currently investigating, 
        # we append the sample according to its rank and move to the next one
        if Y[i,1] == current_id:
            if Y[i,0] == 2:
                rank2.append(copy.deepcopy(X[i]))
            elif Y[i,0] ==1:
                rank1 = copy.deepcopy(X[i])
            
            #if len(sumId) == 0:
            #    sumId = copy.deepcopy(X[i])
            #else:
            #    sumId += copy.deepcopy(X[i])
            
            i += 1
        # If the id doesn't match, then we finished all the samples with the
        # current id, we append the differences (rank1 <-> rank2) in our
        # output and we change the id
        else:
            for r2 in rank2:
                X_new.append((-1)**k * (r2 - rank1)/(r2 + rank1+0.0001))
                Y_new.append((-1)**k)
                Z_new.append(current_id)
                k += 1
            
            rank1 = []
            rank2 = []
            #sumId = []
            current_id = Y[i,1]
    
    # If there is one id which is not in the output        
    if len(rank1) > 0 and len(rank2) > 0:
        for r2 in rank2:
            X_new.append((-1)**k * (r2 - rank1)/(r2 + rank1+0.0001))
            Y_new.append((-1)**k)
            Z_new.append(current_id)
            k += 1

    return np.asarray(X_new), np.asarray(Y_new).ravel(), np.asarray(Z_new).ravel()

class RankSVM(svm.LinearSVC):
    """
    Performs pairwise ranking with an underlying LinearSVC model
    Input should be a n-class ranking problem, this object will convert it
    into a two-class classification problem.
    See object :ref:`svm.LinearSVC` for a full description of parameters
    """    
    def __init__(self):
        self.penalty = 'l2'
        self.loss = 'squared_hinge'
        self.dual = False
        self.tol = 0.0001
        self.C = 1.0
        self.multi_class = 'ovr'
        self.fit_intercept = True
        self.intercept_scaling = 1
        self.class_weight = None
        self.verbose = 0
        self.random_state = np.random.RandomState()
        self.max_iter = 1000
        self.coef_= []
        self.intercept_ = []
    
    def fit(self, X, Y):
        """
        Fit a pairwise ranking model.
        Parameters
        ----------
        X : array, shape (n_samples, n_features)
        y : array, shape (n_samples,) or (n_samples, 2)
        Returns
        -------
        self
        """
        
        X_trans, Y_trans, _ = transform_pairwise(X, Y)
        
        return super().fit(X_trans, Y_trans)

    def predict(self, X):
        """
        Predict an ordering on X. For a list of n samples, this method
        returns a list from 0 to n-1 with the relative order of the rows of X.
        Parameters
        ----------
        X : array, shape (n_samples, n_features)
        Returns
        -------
        ord : array, shape (n_samples,)
            Returns a list of integers representing the relative order of
            the rows in X.
        """
        
        return super().predict(X)
        
        """
        if hasattr(self, 'coef_'):
            np.argsort(np.dot(X, self.coef_.T))
        else:
            raise ValueError("Must call fit() prior to predict()")
        """

    def scoreInversion(self, X, Y):
        """
        Because we transformed into a pairwise problem, chance level is at 0.5
        """
        
        X_trans, Y_trans, _ = transform_pairwise(X, Y)
        
        nb_tot = len(X_trans)   
        pred = (self.predict(X_trans) != Y_trans)
        misclassified = sum(pred)
        
        score = 1 - misclassified/nb_tot
        return score
    
    def scoreId(self, X, Y):
        """
        Because we transformed into a pairwise problem, chance level is at 0.5
        """
        X_trans, Y_trans, Z_trans = transform_pairwise(X, Y)
        
        scoreDict = {}
        
        pred = (self.predict(X_trans) != Y_trans)
        
        for i in range(0,len(X_trans)):
            if not (i in scoreDict) or scoreDict[i]:
                scoreDict[Z_trans[i]] = pred[i]
            
        score = sum(scoreDict.values())/len(scoreDict)
        return score
        #Trouver moyen de bien classer les adresses ensuite
        #Ici critère trop strict
        #Tester méthodes non linéaires à base d'arbres
        #Lifetime fortement corr avec nb_Occurences
        #Liaison vue sur plusieurs sites est-il intéressant ?