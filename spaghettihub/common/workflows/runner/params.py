from dataclasses import dataclass


@dataclass
class SpawnVirtualMachineActivityParams:
    labels: list[str]
    run_id: int
    registration_token: str


@dataclass
class TemporalGithubRunnerWorkflowParams:
    run_id: int
    run_url: str
    labels: list[str]
