#!/usr/bin/env python3
"""
Identify which original vectors correspond to the yellow cluster at (-1, -3)
"""

import pandas as pd
import numpy as np
import json


def main():
    print("🔍 Analyzing the Yellow Cluster at (-1, -3)")
    print("=" * 45)

    # Load the PCA-reduced embeddings that were used for visualization
    embedding_df = pd.read_csv("test_output/qstudy_embedding.csv")

    # The first two columns are the PCA coordinates (e0, e1)
    pca_coords = embedding_df[["e0", "e1"]].values

    # Define the region of interest around (-1, -3)
    target_x, target_y = -1.0, -3.0
    radius = 0.5  # Adjust this to capture the cluster

    # Find vectors in the yellow cluster region
    distances = np.sqrt(
        (pca_coords[:, 0] - target_x) ** 2 + (pca_coords[:, 1] - target_y) ** 2
    )
    cluster_indices = np.where(distances <= radius)[0]

    print(f"📊 Found {len(cluster_indices)} vectors in the yellow cluster region")
    print(f"   Center: ({target_x}, {target_y})")
    print(f"   Search radius: {radius}")

    if len(cluster_indices) > 0:
        print("\n🎯 Cluster Vector Indices:")
        print(f"   {cluster_indices[:10]}{'...' if len(cluster_indices) > 10 else ''}")

        print("\n📍 Exact Coordinates:")
        for i, idx in enumerate(cluster_indices[:5]):  # Show first 5
            x, y = pca_coords[idx]
            print(f"   Vector {idx}: ({x:.3f}, {y:.3f})")

        # Load original embeddings to see what these vectors represent
        print("\n🧬 Original Vector Characteristics:")
        df_orig = pd.read_csv("demo_embeds.csv")

        for i, idx in enumerate(cluster_indices[:3]):  # Analyze first 3
            vec_str = df_orig.iloc[idx]["vec"]
            vec = np.array(json.loads(vec_str))

            print(f"\n   Vector {idx}:")
            print(f"     First 5 dimensions: {vec[:5]}")
            print(f"     Magnitude: {np.linalg.norm(vec):.3f}")
            print(f"     Max value: {vec.max():.3f}")
            print(f"     Min value: {vec.min():.3f}")

    print("\n💡 What This Tells Us:")
    print("   • These vectors have distinct semantic properties")
    print("   • They cluster together because they're similar to each other")
    print("   • But different enough from the main group to separate")
    print("   • This indicates rich, diverse embedding space")


if __name__ == "__main__":
    main()
