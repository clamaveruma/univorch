"""User-facing interfaces: CLI and web GUI.

All interfaces are thin — they translate user input into calls to
OrchestratorService and render the result. No business logic lives here.
Adding a new interface does not require changes to the core.
"""
