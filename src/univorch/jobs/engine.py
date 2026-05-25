"""Jobs engine: runs a Command and records its Job (DEC-028).

The engine assumes the command has already been validated — the
``OrchestratorService`` validates requests and rejects the invalid ones before
any Job is created. The engine owns only the Job lifecycle: persist it as PENDING
before executing, mark it RUNNING, then COMPLETED or FAILED depending on the
execution. Descriptor-state changes (and the future ``broken`` handling) live in
the commands, not here.
"""

from datetime import UTC, datetime

from univorch.jobs.commands import Command
from univorch.models import Job, JobStatus
from univorch.persistence.tinydb.repositories import JobRepository


class JobEngine:
    """Executes commands and persists their Jobs."""

    def __init__(self, jobs_repo: JobRepository) -> None:
        self._jobs = jobs_repo

    def run(self, command: Command) -> Job:
        job = Job(operation_type=command.operation_type, target=command.target)
        self._jobs.save(job)  # persisted as PENDING before executing (DEC-028)
        job.status = JobStatus.RUNNING
        self._jobs.save(job)
        try:
            job.message = command.execute()
            job.status = JobStatus.COMPLETED
        except Exception as error:
            # any execution failure is recorded as a FAILED job
            job.status = JobStatus.FAILED
            job.message = str(error)
        job.finished_at = datetime.now(UTC)
        self._jobs.save(job)
        return job
