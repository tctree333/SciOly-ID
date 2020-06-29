import setuptools


def readme():
    with open("README.md", "r") as f:
        return f.read()


setuptools.setup(
    name="sciolyid",
    version="0.4.7",
    description="Create ID Discord bots for SciOly studying.",
    long_description=readme(),
    long_description_content_type="text/markdown",
    keywords="science_olympiad discord_bot discord studying",
    license="GPLv3+",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.7",
    ],
    url="https://github.com/tctree333/SciOly-ID",
    author="Tomi Chen",
    author_email="tomichen33@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=[
        "discord.py>=1.3.2, <2.0.0",
        "redis>=3.3.5, <4.0.0",
        "sentry-sdk>=0.13.5, <0.16.0",
        "Pillow>=6.1.0, <8.0.0",
        "wikipedia>=1.4.0, <2.0.0",
        "gitpython>=3.0.6, <4.0.0",
        "hiredis>=1.0.1, <1.1.0",
        "pandas>=1.0.0, <1.1.0",
    ],
    py_modules=["config", "core", "data", "functions", "github", "start_bot"],
    python_requires="~=3.7",
)
