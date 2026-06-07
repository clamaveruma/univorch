"""REST interface: FastAPI app over the OrchestratorService facade.

This is a thin interface (DEC-031): each endpoint maps a HTTP request to a
single call on the service and returns its result serialised as JSON. The
service is constructed elsewhere (typically by ``__main__``) and injected
into ``create_app``.

The argument for keeping a REST API is not CLI ergonomics (admins already
have SSH); it is the **public API** for external integrations — scripts,
CI/CD pipelines, GitOps tooling, the future web GUI (Sprint 4). The CLI as
HTTP client is a useful side effect (Sprint 3.2).
"""
