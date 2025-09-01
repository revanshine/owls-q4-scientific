#!/usr/bin/env python3
import pandas as pd
import numpy as np
import json
import time
from q4.svd_ops import center_l2, fit_svd

print("🚀 SVD Optimization Analysis")
print("============================")

# Load demo data
df = pd.read_csv('demo_embeds.csv')
vectors = [json.loads(vec_str) for vec_str in df['vec']]
X = np.array(vectors)
print(f"📊 Data shape: {X.shape}")

Vn, mu = center_l2(X)

# Test different methods
methods = ['truncated', 'randomized', 'auto']
results = {}

for method in methods:
    print(f"\n--- {method.upper()} SVD ---")
    start_time = time.time()
    svd_model = fit_svd(Vn, k=50, method=method)
    elapsed = time.time() - start_time
    
    results[method] = {
        'time': elapsed,
        'components_shape': svd_model.components.shape,
        'top_variance': svd_model.explained_var[:3].tolist()
    }
    
    print(f"⏱️  Time: {elapsed:.3f}s")
    print(f"📐 Components: {svd_model.components.shape}")
    print(f"📈 Top 3 variance: {svd_model.explained_var[:3]}")

print(f"\n🎯 Performance Summary:")
for method, result in results.items():
    print(f"   {method:>12}: {result['time']:.3f}s")

print(f"\n🔍 Result Accuracy Comparison:")
# Use truncated as baseline
baseline = results['truncated']['top_variance']
print(f"{'Method':>12} | {'Time':>8} | {'Max Diff':>10} | {'Mean Diff':>10}")
print("-" * 50)

for method, result in results.items():
    variance = result['top_variance']
    max_diff = max(abs(a - b) for a, b in zip(variance, baseline))
    mean_diff = np.mean([abs(a - b) for a, b in zip(variance, baseline)])
    
    print(f"{method:>12} | {result['time']:>6.3f}s | {max_diff:>8.2e} | {mean_diff:>8.2e}")

print(f"\n📊 Relative Performance:")
fastest_time = min(r['time'] for r in results.values())
for method, result in results.items():
    speedup = result['time'] / fastest_time
    print(f"   {method:>12}: {speedup:.2f}x slower than fastest")

print(f"\n💡 Complexity Improvements:")
print(f"   • TruncatedSVD: O(ndk) vs O(n²d) for full SVD")
print(f"   • Randomized: O(ndk + k³) - best for large datasets")
print(f"   • Auto-selection based on data size")

print(f"\n🧪 Stress Test with Larger Synthetic Data:")
print("=" * 45)

# Create larger synthetic dataset to show differences
np.random.seed(42)
X_large = np.random.randn(1500, 64)  # Larger dataset
Vn_large, mu_large = center_l2(X_large)

print(f"📊 Large data shape: {X_large.shape}")

stress_results = {}
for method in ['truncated', 'randomized']:
    print(f"\n--- {method.upper()} (Large Data) ---")
    start_time = time.time()
    svd_model = fit_svd(Vn_large, k=50, method=method)
    elapsed = time.time() - start_time
    
    stress_results[method] = {
        'time': elapsed,
        'top_variance': svd_model.explained_var[:3].tolist()
    }
    
    print(f"⏱️  Time: {elapsed:.3f}s")
    print(f"📈 Top 3 variance: {svd_model.explained_var[:3]}")

# Compare large data results
print(f"\n🔍 Large Data Accuracy Comparison:")
baseline_large = stress_results['truncated']['top_variance']
randomized_large = stress_results['randomized']['top_variance']

max_diff_large = max(abs(a - b) for a, b in zip(randomized_large, baseline_large))
mean_diff_large = np.mean([abs(a - b) for a, b in zip(randomized_large, baseline_large)])

print(f"   Max difference: {max_diff_large:.2e}")
print(f"   Mean difference: {mean_diff_large:.2e}")
print(f"   Speed improvement: {stress_results['truncated']['time'] / stress_results['randomized']['time']:.2f}x")
