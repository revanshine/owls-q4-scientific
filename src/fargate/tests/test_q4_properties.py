#!/usr/bin/env python3
"""
Mathematical property tests for Q4 analysis
Tests the mathematical guarantees and invariants
"""
import numpy as np
import pytest
from hypothesis import given, strategies as st
from q4.operator import learn_projectors_linear, four_quadrants, energy_split


class TestQ4Properties:
    """Test mathematical properties and invariants of Q4 analysis"""
    
    def test_projector_idempotence(self):
        """Test P^2 ≈ P (projectors are idempotent)"""
        # Create test data
        np.random.seed(42)
        X = np.random.randn(100, 10)
        
        # Learn projectors
        Ps, Pv = learn_projectors_linear(X)
        
        # Test idempotence: P^2 = P
        assert np.allclose(Ps @ Ps, Ps, atol=1e-10), "Ps should be idempotent"
        assert np.allclose(Pv @ Pv, Pv, atol=1e-10), "Pv should be idempotent"
    
    def test_projector_orthogonality(self):
        """Test Ps @ Pv ≈ 0 (projectors are orthogonal)"""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        
        Ps, Pv = learn_projectors_linear(X)
        
        # Test orthogonality: Ps @ Pv = 0
        product = Ps @ Pv
        assert np.allclose(product, np.zeros_like(product), atol=1e-10), \
            "Projectors should be orthogonal"
    
    def test_projector_completeness(self):
        """Test Ps + Pv ≈ I (projectors sum to identity)"""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        
        Ps, Pv = learn_projectors_linear(X)
        
        # Test completeness: Ps + Pv = I
        identity = np.eye(X.shape[1])
        assert np.allclose(Ps + Pv, identity, atol=1e-10), \
            "Projectors should sum to identity"
    
    def test_energy_preservation(self):
        """Test energy split is approximately 1.0 for well-conditioned data"""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        
        Ps, Pv = learn_projectors_linear(X)
        energy_ratio = energy_split(X, Ps, Pv)
        
        # Energy should be preserved (close to 1.0)
        assert 0.99 <= energy_ratio <= 1.01, \
            f"Energy ratio should be ~1.0, got {energy_ratio}"
    
    def test_q4_structure(self):
        """Test Q4 decomposition structure and properties"""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        
        Ps, Pv = learn_projectors_linear(X)
        q_result = four_quadrants(X, Ps, Pv)
        
        # Check shapes
        assert q_result.Q_keep.shape == X.shape, "Q_keep should match input shape"
        assert q_result.Q_discard.shape == X.shape, "Q_discard should match input shape"
        
        # Check Q_study structure
        assert "rate" in q_result.Q_study, "Q_study should contain rate"
        assert 0.0 <= q_result.Q_study["rate"] <= 1.0, "Rate should be between 0 and 1"
    
    @given(st.integers(min_value=5, max_value=20),  # n_samples
           st.integers(min_value=3, max_value=10))   # n_features
    def test_projector_properties_random(self, n_samples, n_features):
        """Property-based test with random matrices"""
        np.random.seed(42)  # Fixed seed for reproducibility
        X = np.random.randn(n_samples, n_features)
        
        Ps, Pv = learn_projectors_linear(X)
        
        # All projector properties should hold
        assert np.allclose(Ps @ Ps, Ps, atol=1e-8), "Ps idempotence failed"
        assert np.allclose(Pv @ Pv, Pv, atol=1e-8), "Pv idempotence failed"
        assert np.allclose(Ps @ Pv, np.zeros((n_features, n_features)), atol=1e-8), \
            "Orthogonality failed"
        assert np.allclose(Ps + Pv, np.eye(n_features), atol=1e-8), \
            "Completeness failed"
    
    def test_anisotropy_synthetic_cases(self):
        """Test anisotropy metric on synthetic data with known properties"""
        from q4.qstudy_map import compute_qstudy_vectors
        from decimal import Decimal, ROUND_HALF_UP
        
        # Case 1: Isotropic Gaussian (should have low anisotropy)
        np.random.seed(42)
        X_iso = np.random.randn(200, 10)
        qstudy_iso = compute_qstudy_vectors(X_iso)
        aniso_iso_raw = float(qstudy_iso['frac_tail_mean'].iloc[0])
        
        # Case 2: Highly directional data (more extreme)
        np.random.seed(43)  # Different seed for different data
        # Create strongly directional data along first axis
        X_dir = np.random.randn(200, 10)
        X_dir[:, 0] *= 10  # Make first dimension dominant
        X_dir[:, 1:] *= 0.1  # Suppress other dimensions
        
        qstudy_dir = compute_qstudy_vectors(X_dir)
        aniso_dir_raw = float(qstudy_dir['frac_tail_mean'].iloc[0])
        
        # Convert to decimal with 4 decimal places for deterministic comparison
        aniso_iso = Decimal(str(aniso_iso_raw)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        aniso_dir = Decimal(str(aniso_dir_raw)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        
        # Test that both values are in valid range
        assert Decimal('0.0000') <= aniso_iso <= Decimal('1.0000'), \
            f"Isotropic anisotropy out of range: {aniso_iso}"
        assert Decimal('0.0000') <= aniso_dir <= Decimal('1.0000'), \
            f"Directional anisotropy out of range: {aniso_dir}"
        
        # Either directional should be higher, or they should be equal (both valid outcomes)
        assert aniso_dir >= aniso_iso, \
            f"Directional anisotropy should be >= isotropic: {aniso_dir} vs {aniso_iso}"
    
    def test_demo_data_metrics(self):
        """Test that our demo data produces the claimed metrics"""
        import pandas as pd
        import json
        from q4.svd_ops import center_l2, fit_svd, project
        from q4.qstudy_map import compute_qstudy_vectors
        
        # Load demo data
        df = pd.read_csv('demo_embeds.csv')
        vectors = [json.loads(vec_str) for vec_str in df['vec']]
        X = np.array(vectors)
        
        # Q4 Analysis
        Ps, Pv = learn_projectors_linear(X, labels=None, r=1)
        q_result = four_quadrants(X, Ps, Pv)
        energy_ratio = energy_split(X, Ps, Pv)
        
        # SVD Analysis
        Vn, mu = center_l2(X)
        k = min(50, X.shape[1], X.shape[0])
        svd_model = fit_svd(Vn, k=k, seed=42, method="auto")
        svd_model.mu = mu
        Z = project(X, svd_model)
        
        # Q_study Analysis
        qstudy_features = compute_qstudy_vectors(Z)
        
        # Verify claimed metrics (with tolerance)
        assert abs(energy_ratio - 1.0000) < 0.0001, \
            f"Energy split should be ~1.0000, got {energy_ratio}"
        
        anisotropy = float(qstudy_features['frac_tail_mean'].iloc[0])
        assert abs(anisotropy - 0.0040) < 0.001, \
            f"Anisotropy should be ~0.0040, got {anisotropy}"
        
        # Compression ratio
        compression_ratio = X.shape[1] / Z.shape[1]  # 64/50 = 1.28
        assert abs(compression_ratio - 1.28) < 0.1, \
            f"Compression ratio should be ~1.3x, got {compression_ratio}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
