from setuptools import find_packages, setup

setup(
    name='launchpadllm',
    version='0.0.1',
    author='Jacopo Rota',
    description='CLI to print the top 10 deb packages that have the most files associated '
                'with them for a certain architecture.',
    python_requires='>=3.5',
    packages=find_packages(include=['launchpadllm', 'launchpadllm.*'],
                           exclude=['*tests*']),
    install_requires=[
        "requests==2.28.1"
    ],
    entry_points={
        'console_scripts': ['launchpadllm=launchpadllm.training.main:main'],
    }
)