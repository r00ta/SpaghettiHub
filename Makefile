.ONESHELL:

DATABASE_NAME := spaghettihub
DATABASE_USER := spaghettihub
DATABASE_PASSWORD := spaghettihub

THIS_DIR := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))

install-dependencies:
	sudo apt-get -y install postgresql python3-venv

setup-postgres:
	sudo -i -u postgres psql -c "CREATE USER \"$(DATABASE_USER)\" WITH ENCRYPTED PASSWORD '$(DATABASE_PASSWORD)'"
	sudo -i -u postgres createdb -O "$(DATABASE_USER)" "$(DATABASE_NAME)"
	sudo sh -c "echo 'host    $(DATABASE_USER)    $(DATABASE_NAME)    0/0     md5' >> /etc/postgresql/14/main/pg_hba.conf"
	sudo systemctl restart postgresql

prepare-ve:
	python3 -m venv $(THIS_DIR)ve
	. $(THIS_DIR)ve/bin/activate
	pip install -r $(THIS_DIR)requirements.txt
	python $(THIS_DIR)setup.py install

migrate:
	. $(THIS_DIR)ve/bin/activate
	alembic upgrade head

setup-temporal:
	sudo snap install --channel=latest/edge temporal-server
	sudo temporal-server.init-sqlite
	sudo snap restart temporal-server

download-temporal-cli:
	wget https://github.com/temporalio/tctl/releases/download/v1.18.0/tctl_1.18.0_linux_amd64.tar.gz -P /tmp
	sudo tar -xvf /tmp/tctl_1.18.0_linux_amd64.tar.gz -C /opt/temporal
	rm /tmp/tctl_1.18.0_linux_amd64.tar.gz

create-temporal-namespace:
	/opt/temporal/tctl --ns default namespace register -rd 3

prod-create-daemons:
	sudo cp $(THIS_DIR)prod/daemons/spaghettihubserver.service /etc/systemd/system/spaghettihubserver.service
	sudo cp $(THIS_DIR)prod/daemons/spaghettihubmpupdate.service /etc/systemd/system/spaghettihubmpupdate.service
	sudo cp $(THIS_DIR)prod/daemons/spaghettihubmpupdate.timer /etc/systemd/system/spaghettihubmpupdate.timer
	sudo cp $(THIS_DIR)prod/daemons/spaghettihubworker.service /etc/systemd/system/spaghettihubworker.service
	sudo systemctl daemon-reload
	sudo systemctl enable spaghettihubserver.service
	sudo systemctl enable spaghettihubmpupdate.service
	sudo systemctl enable spaghettihubmpupdate.timer
	sudo systemctl enable spaghettihubworker.service
	sudo systemctl start spaghettihubserver.service
	sudo systemctl start spaghettihubmpupdate.service
	sudo systemctl start spaghettihubmpupdate.timer
	sudo systemctl start spaghettihubworker.service

lxd-setup:
    openssl req -x509 -newkey rsa:2048 -keyout /home/ubuntu/lxd.key -nodes -out /home/ubuntu/lxd.crt -subj "/CN=10.185.5.1"

setup-production: install-dependencies setup-postgres prepare-ve setup-temporal download-temporal-cli create-temporal-namespace prod-create-daemons prod-create-daemons



git-config:
	git config --global user.name "r00tabot"
	git config --global user.email "r00tabot@gmail.com"

setup-dev: install-dependencies prepare-ve setup-postgres prepare-ve setup-temporal download-temporal-cli create-temporal-namespace

dev-sort:
	. $(THIS_DIR)ve/bin/activate
	isort alembic $(THIS_DIR)spaghettihub

dev-format:
	. $(THIS_DIR)ve/bin/activate
	autopep8 --in-place -r $(THIS_DIR)spaghettihub
	autopep8 --in-place -r $(THIS_DIR)alembic
