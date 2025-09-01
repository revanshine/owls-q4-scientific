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
    df = pd.read_csv('demo_embeds.csv')
    print(f"✅ Loaded {len(df)} embedding vectors")
    
    # Parse vectors
    print("🔄 Parsing embedding vectors...")
    vectors = []
    for vec_str in df['vec']:
        vec = json.loads(vec_str)
        vectors.append(vec)
    
    X = np.array(vectors)
    print(f"✅ Parsed to numpy array: {X.shape}")
    
    # Q4 Analysis
    print("\n🧮 Running Q4 Analysis...")
    Ps, Pv = learn_projectors_linear(X, labels=None, r=1)
    q_result = four_quadrants(X, Ps, Pv)
    energy_ratio = energy_split(X, Ps, Pv)
    
    print(f"✅ Q4 Results:")
    print(f"   Energy split: {energy_ratio:.4f}")
    print(f"   Q_keep shape: {q_result.Q_keep.shape}")
    print(f"   Q_discard shape: {q_result.Q_discard.shape}")
    print(f"   Q_study rate: {q_result.Q_study['rate']:.4f}")
    
    # SVD Analysis
    print("\n🔍 Running SVD Analysis...")
    Vn, mu = center_l2(X)
    k = min(50, X.shape[1], X.shape[0])
    svd_model = fit_svd(Vn, k=k, seed=42)
    svd_model.mu = mu
    Z = project(X, svd_model)
    
    print(f"✅ SVD Results:")
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
    artifacts = embed_reduce_heatmap(qstudy_features, plot_dir, reducer="pca", bins=40)
    
    print(f"✅ Q_study Results:")
    print(f"   Mean absolute value: {float(qstudy_features['mean_absV'].iloc[0]):.4f}")
    print(f"   Energy: {float(qstudy_features['energy'].iloc[0]):.4f}")
    print(f"   Anisotropy (frac_tail_mean): {float(qstudy_features['frac_tail_mean'].iloc[0]):.4f}")
    
    print(f"\n🎨 Visualizations Generated:")
    print(f"   📊 Scatter plot: {artifacts['scatter']}")
    print(f"   🔥 Heatmap: {artifacts['heatmap']}")
    print(f"   📄 Embedding CSV: {artifacts['embedding_csv']}")
    
    print("\n🎉 All scientific analyses completed successfully!")
    print("📊 This demonstrates:")
    print("   ✅ Q4 decomposition working")
    print("   ✅ SVD operations working") 
    print("   ✅ Q_study analytics working")
    print("   ✅ Real embedding data processed")

if __name__ == "__main__":
    main()
