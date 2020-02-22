import setuptools


def readme():
    with open("README.md", "r") as f:
        return f.read()


setuptools.setup(
    name="sciolyid",
    version="0.0.6",
    description="Create ID Discord bots for SciOly studying.",
    long_description=readme(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.7",
    ],
    url="https://github.com/tctree333/SciOly-ID-Discord-Bots",
    author="Tomi Chen",
    author_email="tomichen33@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=[
        "discord.py",
        "redis",
        "sentry-sdk",
        "Pillow",
        "wikipedia",
        "gitpython",
    ],
)
