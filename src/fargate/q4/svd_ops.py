from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import numpy as np


@dataclass
class SVDModel:
    mu: np.ndarray  # (D, )
    components: np.ndarray  # (k, D)
    explained_var: np.ndarray  # (k, )

    def save(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        np.save(path / "mu.npy", self.mu)
        np.save(path / "components.npy", self.components)
        np.save(path / "explained_var.npy", self.explained_var)
        meta = {"dims": int(self.mu.shape[0]), "k": int(self.components.shape[0])}
        (path / "meta.json").write_text(json.dumps(meta, indent=2))

    @staticmethod
    def load(path: Path) -> "SVDModel":
        mu = np.load(path / "mu.npy")
        comps = np.load(path / "components.npy")
        ev = np.load(path / "explained_var.npy")
        return SVDModel(mu=mu, components=comps, explained_var=ev)


def center_l2(
    V: np.ndarray, mu: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray]:
    if mu is None:
        mu = V.mean(axis=0)
    Vc = V - mu
    norms = np.linalg.norm(Vc, axis=1, keepdims=True)
    Vn = Vc / np.maximum(norms, 1e-9)
    return Vn, mu


def fit_svd(
    Vn: np.ndarray, k: int = 50, seed: int = 42, method: str = "auto"
) -> SVDModel:
    """
    Fit SVD with optimized complexity based on data size

    Complexity Analysis:
    - Full SVD: O(min(n²d, nd²)) - expensive for large n
    - TruncatedSVD: O(ndk) - much better when k << min(n,d)
    - Randomized SVD: O(ndk + k³) - fastest for large datasets

    Args:
        method: "auto", "truncated", "randomized", or "incremental"
    """
    n, d = Vn.shape

    # Auto-select method based on data size
    if method == "auto":
        if n > 10000 or d > 1000:
            method = "randomized"  # Best for very large datasets
        elif n > 2000:
            method = "incremental"  # Memory efficient for medium datasets
        else:
            method = "truncated"  # Standard for small-medium datasets

    print(f"Using {method} SVD for shape {Vn.shape}, k={k}")

    if method == "randomized":
        # Randomized SVD: O(ndk + k³) - fastest for large data
        from sklearn.decomposition import TruncatedSVD

        svd = TruncatedSVD(n_components=k, algorithm="randomized", random_state=seed)
        _ = svd.fit_transform(Vn)

    elif method == "incremental":
        # Incremental SVD: O(ndk) memory efficient
        from sklearn.decomposition import IncrementalPCA

        # Note: Using PCA as proxy for incremental SVD
        svd = IncrementalPCA(n_components=k, batch_size=min(1000, n // 4))
        _ = svd.fit_transform(Vn)
        comps = svd.components_
        ev = svd.explained_variance_
        return SVDModel(mu=np.zeros(d), components=comps, explained_var=ev)

    else:  # truncated (default)
        # TruncatedSVD: O(ndk) - good balance
        from sklearn.decomposition import TruncatedSVD

        svd = TruncatedSVD(n_components=k, random_state=seed)
        _ = svd.fit_transform(Vn)

    comps = svd.components_
    ev = svd.explained_variance_
    return SVDModel(mu=np.zeros(d), components=comps, explained_var=ev)


def project(V: np.ndarray, model: SVDModel) -> np.ndarray:
    Vc = V - model.mu
    return Vc @ model.components.T
