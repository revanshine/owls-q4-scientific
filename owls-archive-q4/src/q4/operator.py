
import numpy as np

def learn_projectors_linear(X, labels=None, r=1):
    X = np.asarray(X)
    n,d = X.shape
    if labels is not None:
        classes = np.unique(labels)
        mu = X.mean(axis=0, keepdims=True)
        M = np.vstack([X[labels==c].mean(axis=0)-mu for c in classes])
        _,_,Vt = np.linalg.svd(M, full_matrices=False)
        Bv = Vt[:r].T
    else:
        Xc = X - X.mean(axis=0, keepdims=True)
        _,_,Vt = np.linalg.svd(Xc, full_matrices=False)
        Bv = Vt[:r].T
    Pv = Bv @ Bv.T
    Pv = (Pv + Pv.T)/2
    Ps = np.eye(d) - Pv
    return Ps, Pv

def four_quadrants(X, Ps, Pv):
    X = np.asarray(X)
    S = X @ Ps.T
    V = X @ Pv.T
    muV = V.mean(axis=0, keepdims=True)
    Q_keep = S.copy()
    Q_discard = V - muV
    Q_study = {"mu_V": muV.squeeze().tolist(), "rate": float(np.mean(np.linalg.norm(Q_discard,axis=1)>1e-8))}
    return type("Q", (), {"S":S, "V":V, "Q_keep":Q_keep, "Q_discard":Q_discard, "Q_study":Q_study, "Archive":(S,V)})

def energy_split(X, Ps, Pv):
    S = X @ Ps
    V = X @ Pv
    num = (S**2).sum() + (V**2).sum()
    den = (X**2).sum() + 1e-12
    return float(num/den)
