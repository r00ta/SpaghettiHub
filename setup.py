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
        "requests==2.28.1"
    ],
    entry_points={
        'console_scripts': [
            'lauchpadllm=launchpadllm.training.main:main',
            'launchpadmp=launchpadllm.training.merge_proposals:main',
            'lauchpadllmserver=launchpadllm.server.main:run'
        ],
    },
)