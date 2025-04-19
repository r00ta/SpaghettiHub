import aiohttp
from pylxd import Client
from temporalio import activity

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.models.runner import GithubPushWebhook, GithubWebhook
from spaghettihub.common.services.collection import ServiceCollection
from spaghettihub.common.workflows.base import ActivityBase
from spaghettihub.common.workflows.runner.params import SpawnVirtualMachineActivityParams
from spaghettihub.server.base.db.database import Database


class GithubRunnerActivity(ActivityBase):

    def __init__(self, db: Database, gh_runner_token: str, lxd_host: str, lxd_trusted_password: str):
        super().__init__(db)
        self.gh_runner_token = gh_runner_token
        self.lxd_client = Client(lxd_host, cert=('/home/ubuntu/lxd.crt', '/home/ubuntu/lxd.key'), verify=False)
        self.lxd_client.authenticate(lxd_trusted_password)

    @activity.defn(name="get-registration-token")
    async def get_registration_token(self) -> str:
        url = "https://api.github.com/repos/SpaghettiHub/maas/actions/runners/registration-token"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.gh_runner_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                if not 200 <= int(response.status) < 300:
                    raise RuntimeError(f"Status: {response.status}")
                return (await response.json())["token"]

    @activity.defn(name="spawn-runner")
    async def spawn_runner(self, params: SpawnVirtualMachineActivityParams) -> None:
        """
        TODO: ADD
          - echo 'Acquire::http::Proxy "http://172.0.2.17:8000";' | tee /etc/apt/apt.conf.d/00proxy
          - echo 'http_proxy="http://172.0.2.17:8000/"' | tee /etc/environment
        """
        user_data = f"""
#cloud-config
runcmd:
  - useradd runner
  - mkhomedir_helper runner
  - "echo 'runner ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/runner"
  - usermod -a -G lxd runner
  - su runner -c "git config --global user.name 'r00tabot runner'"
  - su runner -c "git config --global user.email example@example.com"
  - su runner -c "mkdir -p /home/runner/actions-runner"
  - su runner -c "curl -o /home/runner/actions-runner/actions-runner-linux-x64-2.323.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.323.0/actions-runner-linux-x64-2.323.0.tar.gz"
  - su runner -c "echo '0dbc9bf5a58620fc52cb6cc0448abcca964a8d74b5f39773b7afcad9ab691e19  /home/runner/actions-runner/actions-runner-linux-x64-2.323.0.tar.gz' | shasum -a 256 -c"
  - su runner -c "cd /home/runner/actions-runner && tar xzf ./actions-runner-linux-x64-2.323.0.tar.gz"
  - su runner -c "python3 -c 'print(); print(\"{params.id}\")' | /home/runner/actions-runner/config.sh --url https://github.com/SpaghettiHub/maas --token {params.registration_token} --labels {",".join(params.labels)} --ephemeral"
  - su runner -c "/home/runner/actions-runner/run.sh &"
"""
        cpu = "2"
        memory = "4GiB"
        disk =  "8GiB"
        if "medium-runner" in params.labels:
            cpu = "4"
            memory = "8GiB"
            disk = "16GiB"
        if "large-runner" in params.labels:
            cpu = "6"
            memory = "20GiB"
            disk = "50GiB"

        config = {
            "name": self.build_vm_name(params.id),
            "type": "virtual-machine",
            "source": {
                "type": "image",
                "mode": "pull",
                "server": "https://cloud-images.ubuntu.com/releases",
                "protocol": "simplestreams",
                "alias": "24.04",
            },
            "config": {
                "user.user-data": user_data,
                'limits.cpu': cpu,
                'limits.memory': memory
            },
            "devices": {
                "root": {
                    "path": "/",
                    "type": "disk",
                    "size": disk,
                    "pool": "default"
                }
            }
        }
        instance = self.lxd_client.instances.create(config, wait=True)
        instance.start()

    @activity.defn(name="destroy-runner")
    async def destroy_runner(self, id: int) -> None:
        instance = self.lxd_client.instances.get(self.build_vm_name(id))
        instance.stop(force=True)
        instance.delete()

    @activity.defn(name="update-commit-metadata")
    async def update_commit_metadata(self, request: GithubPushWebhook) -> None:
        async with self.start_transaction() as connection:
            connection_provider = ConnectionProvider(
                current_connection=connection)
            services = ServiceCollection.produce(
                connection_provider=connection_provider)
            await services.github_workflow_runner_service.process_push_webhook(request)

    @activity.defn(name="update-continuous-delivery-commit-metadata")
    async def update_continuous_delivery_commit_metadata(self, request: GithubWebhook) -> None:
        async with self.start_transaction() as connection:
            connection_provider = ConnectionProvider(
                current_connection=connection)
            services = ServiceCollection.produce(
                connection_provider=connection_provider)
            await services.github_workflow_runner_service.update_continuous_delivery_commit_metadata(request)

    def build_vm_name(self, id: int) -> str:
        return f"runner-{id}"
