import numpy as np
from src.extraction.extractor import run_extraction
from src.baseline.pca_check import process_tensors
from src.topology.homology import (
    balance_and_subsample, 
    compute_topology, 
    calculate_wasserstein, 
    generate_diagram
)

def main() -> None:
    """
    executes the deterministic topological pipeline.
    """
    print("initiating strict phase 2 pipeline...")
    
    tensors, labels = run_extraction()
    features, expanded_labels = process_tensors(tensors, labels)
    
    features, labels = balance_and_subsample(features, expanded_labels, max_n=200, seed=42)
    
    # isolate regimes
    mask_factual = labels == 0
    mask_inconsistent = labels == 1
    mask_neutral = labels == 2
    
    print("computing vietoris-rips complexes (cosine metric only)...")
    topo_factual = compute_topology(features[mask_factual])
    topo_inconsistent = compute_topology(features[mask_inconsistent])
    topo_neutral = compute_topology(features[mask_neutral])
    
    print("generating persistence diagrams...")
    generate_diagram(topo_factual, "factual")
    generate_diagram(topo_inconsistent, "inconsistent")
    generate_diagram(topo_neutral, "neutral")
    
    # extract h1 (loops) for wasserstein comparison
    h1_factual = topo_factual['dgms'][1]
    h1_inconsistent = topo_inconsistent['dgms'][1]
    h1_neutral = topo_neutral['dgms'][1]
    
    print("\n--- wasserstein distance results (h1 topology) ---")
    w_fact_inc = calculate_wasserstein(h1_factual, h1_inconsistent)
    w_fact_neu = calculate_wasserstein(h1_factual, h1_neutral)
    w_inc_neu = calculate_wasserstein(h1_inconsistent, h1_neutral)
    
    print(f"factual vs inconsistent : {w_fact_inc:.4f}")
    print(f"factual vs neutral      : {w_fact_neu:.4f}")
    print(f"inconsistent vs neutral : {w_inc_neu:.4f}")
    
    print("\n--- conclusion ---")
    if w_fact_inc > max(w_fact_neu, w_inc_neu):
        print("structural separation exists: the inconsistent regime is topologically distinct from the factual baseline.")
    else:
        print("structural separation is weak or non-existent: regimes share highly similar geometric features.")

if __name__ == "__main__":
    main()