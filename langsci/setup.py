import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="langsci",
    version="0.0.19",
    author="Sebastian Nordhoff",
    author_email="sebastian.nordhoff@langsci-press.org",
    description="Tools for open access books used at Language Science Press",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/langsci/pypi",
    packages=["langsci"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)