"""LoRA training tooling for DeckForge AI (milestone M5, Prototype 3).

Training only - no evaluation model is ever imported from here. Similarity
scoring stays a separate offline workload (see ml/evaluation/similarity.py),
because loading a metric encoder inside a measured training process would
inflate exactly the VRAM figures the comparison rests on.
"""
