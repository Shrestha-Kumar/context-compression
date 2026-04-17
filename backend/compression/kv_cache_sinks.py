"""
Attention Sink KV-Cache management.

When the conversation exceeds the model's native context window, the KV-Cache
must be sliced to bound VRAM usage. Naive sliding-window eviction breaks the
attention matrix because autoregressive transformers dump disproportionate
attention mass onto the very first tokens (due to the Softmax normalization).

The fix: always keep the first S tokens (the "attention sinks") AND the most
recent W-S tokens. The middle tokens get evicted. This keeps the model
mathematically stable while bounding VRAM to a fixed window.

Reference: Xiao et al., "Efficient Streaming Language Models with Attention
Sinks" (arXiv 2309.17453).
"""

from typing import Optional
import torch


# HuggingFace Transformers >= 4.36 uses DynamicCache / StaticCache objects
# instead of raw tuples. We handle both.
try:
    from transformers.cache_utils import DynamicCache
    HAS_CACHE_OBJ = True
except ImportError:
    DynamicCache = None
    HAS_CACHE_OBJ = False


def apply_attention_sinks_to_kv_cache(
    past_key_values,
    window_size: int,
    sink_size: int = 4,
):
    """
    Slice the KV-Cache to enforce an Attention Sink window.

    The cache is a per-layer collection of (key_states, value_states) tensors.
    Each tensor has shape [batch_size, num_heads, seq_len, head_dim].
    With Grouped-Query Attention (GQA), num_heads for K/V may be smaller than
    for Q — but the seq_len axis (dim=2) is identical across all cases, so
    our slicing works uniformly.

    Args:
        past_key_values: The cache returned by a prior generate() call.
        window_size: Maximum number of tokens to keep in the cache.
        sink_size: Number of initial tokens to anchor permanently.

    Returns:
        A new cache of the same type with the specified slicing applied.
    """
    if past_key_values is None:
        return None

    if HAS_CACHE_OBJ and isinstance(past_key_values, DynamicCache):
        return _slice_dynamic_cache(past_key_values, window_size, sink_size)

    # Legacy tuple-based cache (older transformers versions)
    return _slice_legacy_tuple_cache(past_key_values, window_size, sink_size)


def _slice_dynamic_cache(
    cache: "DynamicCache",
    window_size: int,
    sink_size: int,
) -> "DynamicCache":
    """Slicing path for HuggingFace's DynamicCache object."""
    if len(cache.key_cache) == 0:
        return cache

    # All layers share the same sequence length
    current_seq_len = cache.key_cache[0].shape[2]
    if current_seq_len <= window_size:
        return cache

    new_cache = DynamicCache()
    for layer_idx in range(len(cache.key_cache)):
        key = cache.key_cache[layer_idx]
        val = cache.value_cache[layer_idx]
        sliced_key, sliced_val = _slice_tensors(key, val, window_size, sink_size)
        # Fresh cache needs explicit update() to register the layer
        new_cache.update(sliced_key, sliced_val, layer_idx)
    return new_cache


def _slice_legacy_tuple_cache(past_key_values, window_size: int, sink_size: int):
    """Slicing path for the legacy tuple-of-tuples cache format."""
    new_kv_cache = []
    for layer in past_key_values:
        key_states, value_states = layer
        current_seq_len = key_states.shape[2]
        if current_seq_len <= window_size:
            new_kv_cache.append((key_states, value_states))
            continue
        sliced_key, sliced_val = _slice_tensors(
            key_states, value_states, window_size, sink_size
        )
        new_kv_cache.append((sliced_key, sliced_val))
    return tuple(new_kv_cache)


def _slice_tensors(
    key_states: torch.Tensor,
    value_states: torch.Tensor,
    window_size: int,
    sink_size: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Core tensor slicing operation.

    Tensor shape: [batch, num_kv_heads, seq_len, head_dim]
    We slice dim=2 (seq_len) to keep [:sink_size] + [-(window_size-sink_size):]
    """
    # Sanity checks
    current_seq_len = key_states.shape[2]
    if current_seq_len <= window_size:
        return key_states, value_states
    if sink_size >= window_size:
        raise ValueError(
            f"sink_size ({sink_size}) must be less than window_size ({window_size})"
        )

    recent_size = window_size - sink_size

    # Sink: first `sink_size` tokens
    sink_keys = key_states[:, :, :sink_size, :]
    sink_values = value_states[:, :, :sink_size, :]

    # Recent: last `recent_size` tokens
    recent_keys = key_states[:, :, -recent_size:, :]
    recent_values = value_states[:, :, -recent_size:, :]

    # Concatenate along sequence dimension
    pruned_keys = torch.cat([sink_keys, recent_keys], dim=2)
    pruned_values = torch.cat([sink_values, recent_values], dim=2)

    return pruned_keys, pruned_values


# -----------------------------------------------------------------------------
# Telemetry helpers
# -----------------------------------------------------------------------------

def cache_seq_len(past_key_values) -> int:
    """Return the current sequence length of the KV cache (0 if empty/None)."""
    if past_key_values is None:
        return 0
    if HAS_CACHE_OBJ and isinstance(past_key_values, DynamicCache):
        if len(past_key_values.key_cache) == 0:
            return 0
        return past_key_values.key_cache[0].shape[2]
    # Legacy tuple
    try:
        return past_key_values[0][0].shape[2]
    except (IndexError, AttributeError):
        return 0


def cache_vram_mb(past_key_values) -> float:
    """Approximate VRAM consumption of the KV cache in megabytes."""
    if past_key_values is None:
        return 0.0
    total_bytes = 0
    if HAS_CACHE_OBJ and isinstance(past_key_values, DynamicCache):
        for k, v in zip(past_key_values.key_cache, past_key_values.value_cache):
            total_bytes += k.numel() * k.element_size()
            total_bytes += v.numel() * v.element_size()
    else:
        for k, v in past_key_values:
            total_bytes += k.numel() * k.element_size()
            total_bytes += v.numel() * v.element_size()
    return total_bytes / (1024 * 1024)
