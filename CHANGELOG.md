# Changelog

## [Added]
- `src/baseline/pca_check.py` implemented for linear baseline validation.
- 2D PCA reduction, variance ratio logging, and silhouette score computation.
- Automated scatter plot generation (`pca_baseline_check.png`).

## [Tested]
- Verified tensor aggregation logic.
- Asserted strict CPU device enforcement to prevent MPS numerical instability.

## [Limitations Observed]
- Token-level aggregation inherently ignores sequence position. If temporal ordering is vital to the regime, PCA on flattened tokens will not capture it.
- Silhouette score computation `O(n^2)` is disabled for token counts exceeding 50,000 to prevent CPU bottlenecking.

## [Changed]
- refactored `src/topology/homology.py` into a strictly linear TDA pipeline.
- replaced comparative visual analysis with quantitative Wasserstein metrics.
- removed `umap-learn` and `sklearn.decomposition.PCA` from the topological pipeline.

## [Tested]
- verified seed determinism guarantees identical Wasserstein outputs across multiple runs.