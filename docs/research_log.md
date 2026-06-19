# Research Log & Architectural Anomalies

## [2026-06-19] PyTorch MPS Backend (Apple Silicon) Matrix Corruption
**Phase:** 0 (Extraction Reality Check)
**Hardware:** MacBook Air M3 (Unified Memory Architecture)

**Observation:**
During initial testing of the extraction pipeline using `TransformerLens` on Apple Silicon, a critical hardware warning was intercepted:
`UserWarning: MPS backend may produce silently incorrect results...`

**Implication for Topological Data Analysis (TDA):**
In standard machine learning inference, minor floating-point imprecision or silent matrix calculation errors might slightly degrade a model's textual output, which is often deemed an acceptable trade-off for speed. However, for this project, the raw hidden states *are* the primary mathematical object. 

TDA relies on computing the Vietoris-Rips complex using exact pairwise distances between points in high-dimensional space. If the `mps` backend introduces silent calculation artefacts into the residual stream tensor, it will warp the true geometric shape of the point cloud. This hardware failure would artificially create or destroy non-contractible loops ($\beta_1$ features), rendering the Wasserstein distance comparisons scientifically invalid.

**Resolution:**
For the integrity of the research, computational speed should be sacrificed for absolute certainty and accuracy with the mathematical calculations. Moving into Phase 1, the architecture will be hardcoded to execute LLM inference strictly on the `cpu`. While this removes the advantage of the M3's GPU acceleration, the CPU backend guarantees mathematically correct tensor extraction, ensuring all observed topological features are genuine properties of the LLM's epistemic state rather than hardware-induced noise.

## [2026-06-19] - Phase 1 Linear Baseline Completion
- Implemented `pca_check.py` to ingest phase 0 extractions.
- Strictly enforced CPU execution to guarantee numerical determinism.
- Built a minimal pipeline to flatten `[sequence_length, d_model]` tensors into a unified token pool.
- Added visual diagnostics and automated silhouette scoring for cluster validation.
- Ready to execute on batch data to determine necessity of Phase 2 (Topology).

### Phase 1 Results & Conclusion ([2026-06-19])
- **Explained Variance (PC1, PC2):** 52.46%, 12.33%
- **Silhouette Score:** -0.1099
- **Interpretation:** The negative silhouette score indicates there to be a cluster overlap and entanglement in lower-dimensional linear space. While the first principal component captures significant variance, linear separation of the factual, inconsistent, and neutral regimes fails.
- **Next Action:** These findings suggest linear geometry is insufficient. We proceed to Phase 2 to apply Topological Data Analysis (TDA), specifically persistent homology, to search for non-linear structural signatures.

