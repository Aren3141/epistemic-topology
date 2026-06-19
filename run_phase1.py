from src.extraction.extractor import run_extraction
from src.baseline.pca_check import process_tensors, run_pca_analysis

def main() -> None:
    """
    orchestrates phase 1 diagnostic pipeline.
    """
    print("initiating phase 1 linear baseline diagnostic...")
    
    # 1. extract tensors via phase 0 pipeline
    tensors, labels = run_extraction()
    
    # 2. process and format for baseline
    features, expanded_labels = process_tensors(tensors, labels)
    
    # 3. execute exploratory statistical reduction
    pca_model, silhouette = run_pca_analysis(features, expanded_labels)
    
    print("phase 1 diagnostic complete. check 'pca_baseline_check.png' for visual results.")

if __name__ == "__main__":
    main()