from setuptools import find_packages, setup

setup(
    name='launchpadllm',
    version='0.0.1',
    author='Jacopo Rota',
    description='CLI to print the top 10 deb packages that have the most files associated '
                'with them for a certain architecture.',
    python_requires='>=3.10',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['**templates/*.html']},
    install_requires=[
        "launchpadlib >= 1.11",
        "keyring >= 23.9",
        "tqdm >= 4.66",
        "torch == 2.2.1",
        "transformers >= 4.34",
        "fastapi >= 0.110.0",
        "uvicorn[standard] >= 0.28.0",
        "jinja2 >= 3.1.2",
        "python-multipart >= 0.0.9",
        "pydantic==2.7.1",
        "asyncpg==0.29.0",
        "SQLAlchemy==2.0.29",
        "alembic==1.13.1",
        "temporalio==1.6.0",
        "itsdangerous==2.2.0",
        "aiohttp==3.9.5"
    ],
    entry_points={
        'console_scripts': [
            'lauchpadllm=launchpadllm.training.main:main',
            'launchpadmp=launchpadllm.training.merge_proposals:main',
            'launchpadllmserver=launchpadllm.server.main:run',
            'launchpadllmworker=launchpadllm.worker.main:run'
        ],
    },
)