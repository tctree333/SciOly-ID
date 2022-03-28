import setuptools


def readme():
    with open("README.md", "r") as f:
        return f.read()


setuptools.setup(
    name="sciolyid",
    version="1.4.1",
    description="Create ID Discord bots for SciOly studying.",
    long_description=readme(),
    long_description_content_type="text/markdown",
    keywords="science_olympiad discord_bot discord studying",
    license="GPLv3+",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    url="https://github.com/tctree333/SciOly-ID",
    author="Tomi Chen",
    author_email="tomichen33@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=[
        "discord.py>=1.7.3, <2.0.0",
        "redis>=3.3.5, <5.0.0",
        "sentry-sdk>=1.1.0, <2.0.0",
        "Pillow>=9.0.1, <10.0.0",
        "wikipedia>=1.4.0, <2.0.0",
        "gitpython>=3.0.6, <4.0.0",
        "hiredis>=1.0.1, <3.0.0",
        "pandas>=1.3.0, <1.5.0",
    ],
    extras_require={
        "web": [
            "filelock>=3.4.2, <3.7.0",
            "Flask>=1.1.2, <2.1.0",
            "Authlib>=0.15.5, <1.0.0",
            "gunicorn>=20.0.4, <21.0.0",
            "ImageHash>=4.0.0, <5.0.0",
            "Celery>=4.4.3, <5.0.0",
            "blinker>=1.4, <1.5",
        ]
    },
    py_modules=["config", "core", "data", "functions", "downloads", "start_bot"],
    python_requires=">=3.7, <=3.10",
)
