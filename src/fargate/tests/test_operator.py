import numpy as np
from q4.operator import learn_projectors_linear, four_quadrants, energy_split


def test_energy_split():
    X = np.random.default_rng(0).normal(size=(100, 4))
    Ps, Pv = learn_projectors_linear(X)
    assert 0.97 <= energy_split(X, Ps, Pv) <= 1.03


def test_quads():
    X = np.random.default_rng(1).normal(size=(50, 3))
    Ps, Pv = learn_projectors_linear(X)
    q = four_quadrants(X, Ps, Pv)
    assert q.Q_keep.shape == X.shape
    assert q.Q_discard.shape == X.shape
