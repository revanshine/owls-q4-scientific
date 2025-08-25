
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .svd_ops import SVDModel

def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def compute_qstudy_vectors(Z: np.ndarray, tail_q: float = 0.997) -> pd.DataFrame:
    tau = np.quantile(np.abs(Z), tail_q, axis=0)
    mean = Z.mean(axis=0)
    std = Z.std(axis=0, ddof=1)
    frac_tail = (np.abs(Z) > tau).mean(axis=0)
    energy = float((Z**2).sum(axis=1).mean())
    feats = {
        "mean_absV": float(np.abs(Z).mean()),
        "std_mean": float(std.mean()),
        "frac_tail_mean": float(frac_tail.mean()),
        "energy": energy,
    }
    for i in range(min(6, Z.shape[1])):
        feats[f"comp{i}_mean"] = float(mean[i])
        feats[f"comp{i}_std"] = float(std[i])
        feats[f"comp{i}_tail"] = float(frac_tail[i])
    return pd.DataFrame([feats])

def embed_reduce_heatmap(qstudy_df: pd.DataFrame, out_dir: Path, reducer: str = "pca", bins: int = 40):
    cols = [c for c in qstudy_df.columns if c not in ("win_id","t_start","t_end")]
    X = qstudy_df[cols].to_numpy()
    if reducer.lower() == "umap":
        try:
            import umap
            X2 = umap.UMAP(n_neighbors=15, min_dist=0.1, n_components=2).fit_transform(X)
        except Exception:
            from sklearn.decomposition import PCA
            X2 = PCA(n_components=2).fit_transform(X)
    else:
        from sklearn.decomposition import PCA
        X2 = PCA(n_components=2).fit_transform(X)
    qstudy_df = qstudy_df.copy()
    qstudy_df["e0"] = X2[:,0]; qstudy_df["e1"] = X2[:,1]
    scatter_path = out_dir / "qstudy_scatter.png"
    ensure_parent(scatter_path)
    plt.figure(figsize=(6,5))
    sc = plt.scatter(qstudy_df["e0"], qstudy_df["e1"], c=qstudy_df["frac_tail_mean"], s=30)
    plt.colorbar(sc, label="frac_tail_mean")
    plt.xlabel("embed-0"); plt.ylabel("embed-1"); plt.title("Q_study embedding")
    plt.tight_layout(); plt.savefig(scatter_path); plt.close()

    H_count, xedges, yedges = np.histogram2d(qstudy_df["e0"], qstudy_df["e1"], bins=bins)
    H_val, _, _ = np.histogram2d(qstudy_df["e0"], qstudy_df["e1"], bins=[xedges, yedges], weights=qstudy_df["frac_tail_mean"])
    H_mean = H_val / np.maximum(H_count, 1)
    heatmap_path = out_dir / "qstudy_heatmap.png"
    plt.figure(figsize=(6,5))
    plt.imshow(H_mean.T, origin="lower", extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], aspect="auto")
    plt.xlabel("embed-0"); plt.ylabel("embed-1"); plt.title("Q_study anisotropy heatmap (mean frac_tail)")
    plt.tight_layout(); plt.savefig(heatmap_path); plt.close()
    (out_dir / "qstudy_embedding.csv").write_text(qstudy_df.to_csv(index=False))
    return {"scatter": str(scatter_path), "heatmap": str(heatmap_path), "embedding_csv": str(out_dir / "qstudy_embedding.csv")}
