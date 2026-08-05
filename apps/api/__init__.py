"""DeckForge AI backend service (M7 / Prototype 5).

Thin HTTP layer in front of the generation stack Prototypes 3 and 4 measured. It
adds no modelling of its own: the base model, the adapters, the conditioning
method and their settings all come from the decision records, and the generation
call reuses `ml.inference` and `ml.training` code unchanged.
"""
