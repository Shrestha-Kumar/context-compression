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
    # Transformers < 4.47 used key_cache/value_cache attributes.
    # Transformers 4.47+ uses the .layers attribute (list of DynamicLayer).
    # We use getattr to be safe across both.
    
    key_cache = getattr(cache, "key_cache", None)
    value_cache = getattr(cache, "value_cache", None)
    layers = getattr(cache, "layers", None)

    if layers is not None:
        # Modern path (4.47+)
        if len(layers) == 0:
            return cache
        current_seq_len = layers[0].keys.shape[2]
        if current_seq_len <= window_size:
            return cache
        
        from transformers.cache_utils import DynamicCache
        new_cache = DynamicCache()
        for layer_idx, layer in enumerate(layers):
            sliced_key, sliced_val = _slice_tensors(layer.keys, layer.values, window_size, sink_size)
            new_cache.update(sliced_key, sliced_val, layer_idx)
        return new_cache

    elif key_cache is not None:
        # Legacy path (4.36 - 4.46)
        if len(key_cache) == 0:
            return cache
        current_seq_len = key_cache[0].shape[2]
        if current_seq_len <= window_size:
            return cache

        from transformers.cache_utils import DynamicCache
        new_cache = DynamicCache()
        for layer_idx in range(len(key_cache)):
            key = key_cache[layer_idx]
            val = value_cache[layer_idx]
            sliced_key, sliced_val = _slice_tensors(key, val, window_size, sink_size)
            new_cache.update(sliced_key, sliced_val, layer_idx)
        return new_cache

    return cache


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
        layers = getattr(past_key_values, "layers", None)
        key_cache = getattr(past_key_values, "key_cache", None)
        
        if layers is not None and len(layers) > 0:
            return layers[0].keys.shape[2]
        if key_cache is not None and len(key_cache) > 0:
            return key_cache[0].shape[2]
        return 0
    # Legacy tuple
    try:
        return past_key_values[0][0].shape[2]
    except (IndexError, AttributeError, TypeError):
        return 0


def cache_vram_mb(past_key_values) -> float:
    """Approximate VRAM consumption of the KV cache in megabytes."""
    if past_key_values is None:
        return 0.0
    total_bytes = 0
    if HAS_CACHE_OBJ and isinstance(past_key_values, DynamicCache):
        layers = getattr(past_key_values, "layers", None)
        key_cache = getattr(past_key_values, "key_cache", None)
        value_cache = getattr(past_key_values, "value_cache", None)

        if layers is not None:
            for layer in layers:
                total_bytes += layer.keys.numel() * layer.keys.element_size()
                total_bytes += layer.values.numel() * layer.values.element_size()
        elif key_cache is not None and value_cache is not None:
            for k, v in zip(key_cache, value_cache):
                total_bytes += k.numel() * k.element_size()
                total_bytes += v.numel() * v.element_size()
    else:
        try:
            for k, v in past_key_values:
                total_bytes += k.numel() * k.element_size()
                total_bytes += v.numel() * v.element_size()
        except (TypeError, ValueError):
            pass
    return total_bytes / (1024 * 1024)
