import numpy as np
from q4.operator import learn_projectors_linear, energy_split

def main():
    np.random.seed(42)
    X = np.random.randn(50, 10)
    Ps, Pv = learn_projectors_linear(X)

    # Core properties
    assert np.allclose(Ps @ Ps, Ps, atol=1e-8), "Idempotence failed"
    assert np.allclose(Ps @ Pv, np.zeros_like(Ps), atol=1e-8), "Orthogonality failed"
    assert np.allclose(Ps + Pv, np.eye(10), atol=1e-8), "Completeness failed"

    energy = energy_split(X, Ps, Pv)
    assert 0.99 <= energy <= 1.01, f"Energy preservation failed: {energy}"

    print("✅ All mathematical guarantees validated!")

if __name__ == "__main__":
    main()
