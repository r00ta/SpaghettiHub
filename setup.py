from setuptools import find_packages, setup

setup(
    name='spaghettihub',
    version='0.0.1',
    author='Jacopo Rota',
    description='My productivity tools for Launchpad and GitHub',
    python_requires='>=3.10',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['**templates/*.html']},
    install_requires=[
        # use pip dude
    ],
    entry_points={
        'console_scripts': [
            'spaghettihubtraining=spaghettihub.training.main:main',
            'spaghettihubmergeproposals=spaghettihub.training.merge_proposals:main',
            'spaghettihubserver=spaghettihub.server.main:run',
            'spaghettihubworker=spaghettihub.worker.main:run'
        ],
    },
)