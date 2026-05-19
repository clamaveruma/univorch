"""Persistence layer: Repository pattern.

Repository interfaces (ABCs) are defined in base.py.
Concrete implementations live in subpackages (tinydb/, mongo/ in the future).
The rest of the application depends only on the interfaces — never on TinyDB directly.
This is what makes it possible to swap the database without touching business logic.
"""
