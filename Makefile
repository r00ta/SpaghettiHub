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

download-temporal:
	sudo mkdir /opt/temporal
	wget https://github.com/temporalio/temporal/releases/download/v1.23.1/temporal_1.23.1_linux_amd64.tar.gz -P /tmp
	sudo tar -xvf /tmp/temporal_1.23.1_linux_amd64.tar.gz -C /opt/temporal
	rm /tmp/temporal_1.23.1_linux_amd64.tar.gz

setup-temporal-database:
	sudo git clone --branch release/v1.23.x https://github.com/temporalio/temporal.git /opt/temporal/temporal_src/

	export SQL_PLUGIN=postgres
	export SQL_HOST=localhost
	export SQL_PORT=5432
	export SQL_USER=spaghettihub
	export SQL_PASSWORD=spaghettihub

	sudo -u postgres psql -c "ALTER USER $(DATABASE_USER) WITH SUPERUSER;"
	/opt/temporal/temporal-sql-tool --database temporal create-database
	SQL_DATABASE=temporal /opt/temporal/temporal-sql-tool setup-schema -v 0.0
	SQL_DATABASE=temporal /opt/temporal/temporal-sql-tool update -schema-dir /opt/temporal/temporal_src/schema/postgresql/v12/temporal/versioned

	/opt/temporal/temporal-sql-tool --database temporal_visibility create-database
	SQL_DATABASE=temporal_visibility /opt/temporal/temporal-sql-tool setup-schema -v 0.0
	SQL_DATABASE=temporal_visibility /opt/temporal/temporal-sql-tool update -schema-dir /opt/temporal/temporal_src/schema/postgresql/v12/visibility/versioned
	sudo -u postgres psql -c "ALTER USER $(DATABASE_USER) WITH NOSUPERUSER;"

	sudo cp /opt/temporal/config/development-postgres.yaml /opt/temporal/config/development.yaml
	sudo sed -i 's/"temporal"/"$(DATABASE_USER)"/g' /opt/temporal/config/development.yaml


download-temporal-cli:
	wget https://github.com/temporalio/tctl/releases/download/v1.18.0/tctl_1.18.0_linux_amd64.tar.gz -P /tmp
	sudo tar -xvf /tmp/tctl_1.18.0_linux_amd64.tar.gz -C /opt/temporal
	rm /tmp/tctl_1.18.0_linux_amd64.tar.gz

create-temporal-namespace:
	/opt/temporal/tctl --ns default namespace register -rd 3

prod-create-daemons:
	sudo cp $(THIS_DIR)prod/daemons/spaghettihubserver.service /etc/systemd/system/spaghettihubserver.service
	sudo cp $(THIS_DIR)prod/daemons/spaghettihubmpupdate.service /etc/systemd/system/spaghettihubmpupdate.service
	sudo cp $(THIS_DIR)prod/daemons/spaghettihubworker.service /etc/systemd/system/spaghettihubworker.service
	sudo cp $(THIS_DIR)prod/daemons/temporal.service /etc/systemd/system/temporal.service
	sudo systemctl daemon-reload
	sudo systemctl enable spaghettihubserver.service
	sudo systemctl enable spaghettihubmpupdate.service
	sudo systemctl enable spaghettihubworker.service
	sudo systemctl enable temporal.service
	sudo systemctl start spaghettihubserver.service
	sudo systemctl start spaghettihubmpupdate.service
	sudo systemctl start spaghettihubworker.service
	sudo systemctl start temporal.service


setup-production: install-dependencies setup-postgres prepare-ve download-temporal setup-temporal-database download-temporal-cli create-temporal-namespace prod-create-daemons prod-create-daemons



git-config:
	git config --global user.name "r00tabot"
	git config --global user.email "r00tabot@gmail.com"

setup-dev: install-dependencies prepare-ve setup-postgres prepare-ve download-temporal setup-temporal-database download-temporal-cli create-temporal-namespace

dev-start-temporal:
	/opt/temporal/temporal-server -r $(THIS_DIR)prod -c temporal_config start

dev-sort:
	. $(THIS_DIR)ve/bin/activate
	isort alembic $(THIS_DIR)spaghettihub

dev-format:
	. $(THIS_DIR)ve/bin/activate
	autopep8 --in-place -r $(THIS_DIR)spaghettihub
	autopep8 --in-place -r $(THIS_DIR)alembic
