import torch
from transformer_lens import HookedTransformer
from typing import List, Tuple

class ResidualStreamExtractor:
    """
    manages hidden state extraction from language models using transformer_lens.
    safeguards system memory by enforcing strict token length limits.
    """
    
    def __init__(self, model_name: str = "gpt2-small", device: str = "cpu"):
        """
        initialises the transformer instance and targets the system hardware.
        """
        print(f"loading target model: {model_name} onto processing device: {device}...")
        self.device = device
        self.model = HookedTransformer.from_pretrained(model_name, device=self.device)
        self.d_model = self.model.cfg.d_model
        self.n_layers = self.model.cfg.n_layers
        print(f"model loaded. model dimension: {self.d_model}, total layers: {self.n_layers}")

    def extract_final_layer(self, prompt: str) -> torch.Tensor:
        """
        routes text through the model to extract the final residual stream state.
        enforces strict length limits to protect the downsampling pipeline.
        """
        tokens = self.model.to_tokens(prompt)
        seq_len = tokens.shape[1]
        
        # strict bounding condition to prevent computational scale explosions later
        if seq_len > 200:
            raise ValueError(f"sequence length of {seq_len} tokens exceeds the maximum cap of 200.")
            
        print(f"processing target prompt: '{prompt}' (sequence spans {seq_len} tokens)")

        # tracking the final layer index using zero-indexed notation
        final_layer_idx = self.n_layers - 1
        hook_name = f"blocks.{final_layer_idx}.hook_resid_post"

        # run forward pass while caching only our designated layer slice
        logits, cache = self.model.run_with_cache(
            tokens, 
            names_filter=lambda name: name == hook_name
        )

        # isolate the specific activation matrix and strip the batch dimension
        hidden_states = cache[hook_name].squeeze(0)
        
        return hidden_states

def run_extraction() -> Tuple[List[torch.Tensor], List[int]]:
    """
    generates a small exploratory batch of tensors and labels for the phase 1 diagnostic.
    """
    # strictly bind to cpu to guarantee reproducible geometry
    extractor = ResidualStreamExtractor(model_name="gpt2-small", device="cpu")
    
    # minimal sample data to test linear separability across regimes
    prompts = [
        "The capital of France is Paris.",         
        "The capital of France is a spaceship.",   
        "The weather today is fairly mild."        
    ]
    
    # corresponding diagnostic labels
    # 0: factual, 1: inconsistent, 2: neutral
    labels = [0, 1, 2]
    tensors = []
    
    for prompt in prompts:
        tensors.append(extractor.extract_final_layer(prompt))
        
    return tensors, labels

if __name__ == "__main__":
    # strict cpu enforcement to prevent numerical drift
    target_device = "cpu"
    
    extractor = ResidualStreamExtractor(model_name="gpt2-small", device=target_device)
    test_prompt = "The capital of France is Paris."
    
    try:
        tensor_output = extractor.extract_final_layer(test_prompt)
        
        expected_seq_len = extractor.model.to_tokens(test_prompt).shape[1]
        expected_d_model = extractor.d_model
        
        print("\n--- extraction execution report ---")
        print(f"captured tensor dimensions: {tensor_output.shape}")
        
        # confirm our structural data grid aligns perfectly with expected architecture
        assert tensor_output.shape == (expected_seq_len, expected_d_model), "tensor footprint mismatch detected"
        print("validation clean. shape array maps to sequence matrix matches.")
        
    except Exception as error:
        print(f"extraction loop failed to resolve: {error}")