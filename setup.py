from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()
    
try:
    with open("requirements.txt", "r") as req_file:
        install_requires = req_file.read().splitlines()
except FileNotFoundError:
    install_requires = []  # If requirements.txt is missing, no dependencies

setup(
    name="your_project_name",
    version="0.1.0",
    author="Glavin Lobo",
    author_email="glavinlobo92@gmail.com",
    description="A short description of your project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=install_requires
)
