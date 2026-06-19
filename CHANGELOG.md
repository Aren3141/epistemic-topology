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