from dataclasses import dataclass


@dataclass
class SpawnVirtualMachineActivityParams:
    labels: list[str]
    id: int
    registration_token: str


@dataclass
class TemporalGithubRunnerWorkflowParams:
    id: int
    run_url: str
    labels: list[str]
