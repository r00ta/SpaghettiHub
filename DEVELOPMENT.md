# Development

This document contains the instructions to setup your environment for development 

## Environment

Install LXD

```
sudo snap install lxd --channel=latest/stable
sudo lxd init --auto
```

Launch a new LXD container with 

```sh
lxc launch ubuntu:22.04 spaghettihub
```

Login into the container 

```sh
lxc shell spaghettihub
su ubuntu
```

Clone this repository 
```sh
git clone https://github.com/r00ta/SpaghettiHub.git ~/
```

## Setup
```sh
cd ~/spaghettihub
sudo apt get make python3-venv
make setup-dev
```

Configure git (you might want to replace the hardcoded username/email in the makefile!)

```sh
make git-config
```

You can now start the temporal server

```sh
make dev-start-temporal
```

the temporal worker
```sh
spaghettihubworker --gh_token <gh_token>
```

and the server
```sh
spaghettihubserver
```

Please note that some configurations are hardcoded. Contributions to make the code generic are more than welcome
