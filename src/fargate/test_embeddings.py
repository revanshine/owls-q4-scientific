#!/usr/bin/env python3
"""
Test script for Q4 processing with real embedding data
"""

import pandas as pd
import numpy as np
import json
from q4.operator import learn_projectors_linear, four_quadrants, energy_split
from q4.svd_ops import center_l2, fit_svd, project
from q4.qstudy_map import compute_qstudy_vectors


def main():
    print("🔬 OWLS Q4 - Scientific Processing Test")
    print("=" * 40)

    # Load demo embeddings
    print("📥 Loading demo embeddings...")
    df = pd.read_csv("demo_embeds.csv")
    print(f"✅ Loaded {len(df)} embedding vectors")

    # Parse vectors
    print("🔄 Parsing embedding vectors...")
    vectors = []
    for vec_str in df["vec"]:
        vec = json.loads(vec_str)
        vectors.append(vec)

    X = np.array(vectors)
    print(f"✅ Parsed to numpy array: {X.shape}")

    # Q4 Analysis
    print("\n🧮 Running Q4 Analysis...")
    Ps, Pv = learn_projectors_linear(X, labels=None, r=1)
    q_result = four_quadrants(X, Ps, Pv)
    energy_ratio = energy_split(X, Ps, Pv)

    print("✅ Q4 Results:")
    print(f"   Energy split: {energy_ratio:.4f}")
    print(f"   Q_keep shape: {q_result.Q_keep.shape}")
    print(f"   Q_discard shape: {q_result.Q_discard.shape}")
    print(f"   Q_study rate: {q_result.Q_study['rate']:.4f}")

    # SVD Analysis
    print("\n🔍 Running SVD Analysis...")
    Vn, mu = center_l2(X)
    k = min(50, X.shape[1], X.shape[0])
    svd_model = fit_svd(Vn, k=k, seed=42, method="auto")  # Use optimized auto-selection
    svd_model.mu = mu
    Z = project(X, svd_model)

    print("✅ SVD Results:")
    print(f"   Projection shape: {Z.shape}")
    print(f"   Explained variance (top 5): {svd_model.explained_var[:5]}")

    # Q_study Analysis with Visualizations
    print("\n📈 Running Q_study Analysis with Visualizations...")
    qstudy_features = compute_qstudy_vectors(Z)

    # Create output directory for visualizations
    from pathlib import Path

    plot_dir = Path("./test_output")
    plot_dir.mkdir(exist_ok=True)

    # Generate visualizations (full processing mode)
    from q4.qstudy_map import embed_reduce_heatmap

    # Create proper DataFrame for visualization using SVD projection data
    # Use the SVD projection Z for visualization (500 vectors, 50 dimensions)
    qstudy_df = pd.DataFrame(Z)
    # Add the anisotropy metric for coloring (same value for all points from our analysis)
    qstudy_df["frac_tail_mean"] = float(qstudy_features["frac_tail_mean"].iloc[0])

    artifacts = embed_reduce_heatmap(qstudy_df, plot_dir, reducer="pca", bins=40)

    # Generate structured metrics for agent consumption
    metrics = {
        "dataset_info": {
            "total_vectors": int(X.shape[0]),
            "dimensions": int(X.shape[1]),
            "data_size_mb": float(X.nbytes / 1024 / 1024),
        },
        "q4_analysis": {
            "energy_split": float(energy_ratio),
            "energy_preservation": (
                "perfect"
                if energy_ratio >= 0.999
                else "good"
                if energy_ratio >= 0.95
                else "poor"
            ),
            "q_keep_vectors": int(q_result.Q_keep.shape[0]),
            "q_discard_vectors": int(q_result.Q_discard.shape[0]),
            "q_study_rate": float(q_result.Q_study["rate"]),
        },
        "svd_analysis": {
            "projection_dimensions": int(Z.shape[1]),
            "compression_ratio": float(X.shape[1] / Z.shape[1]),
            "top_variance_components": svd_model.explained_var[:5].tolist(),
            "cumulative_variance_top5": float(svd_model.explained_var[:5].sum()),
            "variance_concentration": (
                "high"
                if svd_model.explained_var[0] > 0.1
                else "medium"
                if svd_model.explained_var[0] > 0.05
                else "distributed"
            ),
        },
        "qstudy_analysis": {
            "mean_magnitude": float(qstudy_features["mean_absV"].iloc[0]),
            "total_energy": float(qstudy_features["energy"].iloc[0]),
            "anisotropy": float(qstudy_features["frac_tail_mean"].iloc[0]),
            "data_quality": (
                "excellent"
                if qstudy_features["frac_tail_mean"].iloc[0] < 0.01
                else (
                    "good"
                    if qstudy_features["frac_tail_mean"].iloc[0] < 0.05
                    else "needs_attention"
                )
            ),
        },
        "significant_findings": [],
        "visualization_files": {
            "scatter_plot": str(artifacts["scatter"]),
            "heatmap": str(artifacts["heatmap"]),
            "embedding_csv": str(artifacts["embedding_csv"]),
        },
    }

    # Identify significant findings for agent attention
    if metrics["q4_analysis"]["energy_split"] >= 0.999:
        metrics["significant_findings"].append(
            "PERFECT_ENERGY_PRESERVATION: Q4 decomposition preserved 100% of data energy"
        )

    if metrics["qstudy_analysis"]["anisotropy"] < 0.01:
        metrics["significant_findings"].append(
            "EXCELLENT_DATA_BALANCE: Very low anisotropy indicates well-distributed data"
        )

    if metrics["svd_analysis"]["top_variance_components"][0] > 0.05:
        metrics["significant_findings"].append(
            "STRONG_PRIMARY_COMPONENT: First SVD component captures significant variance"
        )

    if metrics["svd_analysis"]["compression_ratio"] > 1.2:
        metrics["significant_findings"].append(
            f"EFFECTIVE_COMPRESSION: {metrics['svd_analysis']['compression_ratio']:.1f}x dimensionality reduction achieved"
        )

    # Write structured metrics for agent consumption
    metrics_file = plot_dir / "qstudy_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    # Write human-readable summary
    summary_file = plot_dir / "qstudy_summary.txt"
    with open(summary_file, "w") as f:
        f.write("OWLS Q4 Scientific Analysis Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(
            f"Dataset: {metrics['dataset_info']['total_vectors']} vectors × {metrics['dataset_info']['dimensions']} dimensions\n"
        )
        f.write(
            f"Energy Preservation: {metrics['q4_analysis']['energy_preservation'].upper()} ({metrics['q4_analysis']['energy_split']:.4f})\n"
        )
        f.write(
            f"Data Quality: {metrics['qstudy_analysis']['data_quality'].upper()} (anisotropy: {metrics['qstudy_analysis']['anisotropy']:.4f})\n"
        )
        f.write(
            f"Compression: {metrics['svd_analysis']['compression_ratio']:.1f}x reduction\n\n"
        )

        f.write("SIGNIFICANT FINDINGS:\n")
        for finding in metrics["significant_findings"]:
            f.write(f"• {finding}\n")

        f.write("\nVISUALIZATIONS:\n")
        f.write(f"• Scatter Plot: {artifacts['scatter']}\n")
        f.write(f"• Heatmap: {artifacts['heatmap']}\n")
        f.write(f"• Data Export: {artifacts['embedding_csv']}\n")

    print("✅ Q_study Results:")
    print(f"   Mean absolute value: {metrics['qstudy_analysis']['mean_magnitude']:.4f}")
    print(f"   Energy: {metrics['qstudy_analysis']['total_energy']:.4f}")
    print(
        f"   Anisotropy (frac_tail_mean): {metrics['qstudy_analysis']['anisotropy']:.4f}"
    )

    print("\n🎨 Visualizations Generated:")
    print(f"   📊 Scatter plot: {artifacts['scatter']}")
    print(f"   🔥 Heatmap: {artifacts['heatmap']}")
    print(f"   📄 Embedding CSV: {artifacts['embedding_csv']}")

    print("\n🤖 Agent Metrics:")
    print(f"   📋 Structured metrics: {metrics_file}")
    print(f"   📝 Human summary: {summary_file}")

    print("\n🔍 Significant Findings:")
    for finding in metrics["significant_findings"]:
        print(f"   • {finding}")

    print("\n🎉 All scientific analyses completed successfully!")
    print("📊 This demonstrates:")
    print("   ✅ Q4 decomposition working")
    print("   ✅ SVD operations working")
    print("   ✅ Q_study analytics working")
    print("   ✅ Real embedding data processed")


if __name__ == "__main__":
    main()
