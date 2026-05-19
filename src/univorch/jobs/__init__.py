"""Job engine: Command pattern, lifecycle, and locking.

Every operation (deploy, start, stop…) is a Command object with
validate() and execute() methods. The engine persists Jobs to the
database before running them so the state survives a crash.
"""
