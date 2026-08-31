"""Repository-owned test namespace.

This explicit package boundary prevents unrelated distributions that install a
top-level ``tests`` package from shadowing intra-suite imports in clean clones.
"""
