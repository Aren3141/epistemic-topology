# The Epistemic Topology Project

### Topological Comparison of Generation Regimes in LLM Latent Spaces

---

## 1. Abstract

This project introduces an exploratory diagnostic framework utilising Topological Data Analysis (TDA) to compare the structural properties of latent spaces within Large Language Models (LLMs). We investigate whether specific generation regimes, such as prompts with a higher likelihood of factual inconsistency, correlate with distinct geometric signatures within the network residual stream. 

We propose to measure whether conflicting semantic states during generation manifest as non-contractible loops ($\beta_1$ features) within the token-layer manifold. By computing the Wasserstein distance between persistence diagrams of different generation pathways, we treat these topological invariants as descriptive indicators to map and understand structural variations in latent representations.

---

## 2. The Mathematical Object: The Point Cloud

We define our topological space by extracting a finite point cloud from the structured trajectory of hidden states across temporal evolution (token generation steps) and hierarchical depth (transformer layers).

Let $h_{t,l}$ be the hidden state vector at token generation step $t$ and network layer $l$. Assuming a transformer with $L$ layers, a sequence length of $T$ tokens, and a hidden dimension $d$, a raw extraction yields a massive point cloud:

$$X_{raw} = \{h_{t,l} \in \mathbb{R}^d \mid 1 \le t \le T, 0 \le l \le L\}$$

### The Downsampling Constraint
Computing a Vietoris-Rips complex directly on $X_{raw}$ scales exponentially, making the computation unstable and resource-prohibitive. To prevent system memory collapse, we apply strict downsampling strategies to ensure our final point cloud $X \in \mathbb{R}^{N \times d}$ adheres to the constraint $N \le 200$:

* **Temporal Selection:** Isolate a strict sliding window of $5$ to $10$ tokens surrounding the specific moment of output divergence.
* **Structural Selection:** Extract only a predefined subset of key intermediate and final layers rather than the entire network depth.

---

## 3. Distance Metrics as Experimental Variables

The latent space of LLMs is known to be anisotropic; embeddings often occupy a narrow, directional cone within high-dimensional space. To remain scientifically objective, we do not assume a single metric is correct. We treat the proximity calculation as an experimental variable, executing our filtration loops across two distinct distance functions:

### Standard Euclidean Distance ($L_2$)
$$d_{euc}(x,y) = \sqrt{\sum_{i=1}^d (x_i - y_i)^2}$$

### Cosine Distance
$$d_{cos}(x,y) = 1 - \frac{x \cdot y}{\|x\|_2 \|y\|_2}$$

---

## 4. Linear Baseline Check (PCA Validation)

Before applying complex topological methods, every extracted point cloud must undergo a linear baseline analysis using Principal Component Analysis (PCA). 

Fundamentally, if simple linear clustering or dimensionality reduction shows a clear structural distinction between generation regimes, the computational overhead of TDA is unjustified. TDA should only be leveraged if the underlying structural differences are non-linear, geometrically twisted, or completely obscured during standard projection.

---

## 5. Experimental Controls and Prompting Regimes

To isolate structural signatures from general language complexity, we evaluate our model using strict greedy decoding ($\text{temperature} = 0$). This parameter constraint is used to ensure absolute mathematical reproducibility and remove token-sampling noise; it does not imply an absolute isolation of cognitive mechanics.

We evaluate performance across three distinct prompting categories derived from benchmarks like TruthfulQA:

| Regime | Description | Expected Output Behaviour |
| :--- | :--- | :--- |
| **Factual Baseline** | High-confidence prompts mapping to verified ground truths. | Clean, direct semantic convergence. |
| **Inconsistent Target** | Prompts engineered to exploit common misconceptions or induce false retrieval. | Confident generation of incorrect outputs. |
| **Neutral Control** | Abstract, subjective, or philosophical prompts lacking binary truth targets. | Structurally complex but non-factual generation. |

---

## 6. Target Metrics: Persistence Diagrams and Wasserstein Distance

We do not look at single, isolated Betti counts. Instead, we track how topological features are born and die across an evolving filtration distance, producing a full persistence diagram:

$$\phi(X) = \text{Persistence Diagram of } X$$

To determine if a true geometric divergence occurs between standard generation and factually inconsistent states, we calculate the Wasserstein Distance ($W_p$) between their respective diagrams:

$$W_p(D_1,D_2) = \left( \inf_{\gamma} \sum_{x \in D_1} \|x - \gamma(x)\|_{\infty}^p \right)^{1/p}$$

Where $\gamma$ represents the matching bijection between diagram points. 

### The Shuffled Null Distribution
To validate our results, all Wasserstein distances are evaluated against a null distribution created by randomly shuffling the layer and token identities of our extracted tensors. If the distance measured between our true experimental blocks does not sit significantly outside this shuffled baseline, any observed $\beta_1$ loops must be categorised as statistical noise rather than genuine architectural properties.

### Phase 1: Linear Baseline Validation
We apply Principal Component Analysis (PCA) directly to the CPU-extracted residual streams. This phase is diagnostic. The results generated here are exploratory and do not prove causation. If the regimes (factual, inconsistent, neutral) separate cleanly in two dimensions, it suggests linear mechanisms comprise the representation. If they remain entangled, it is consistent with the hypothesis that higher-dimensional or topological manifolds are required to distinguish the epistemic states.