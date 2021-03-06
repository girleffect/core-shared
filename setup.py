from setuptools import setup, find_packages

LONG_DESCRIPTION_FILES = ["README.rst", "AUTHORS.rst", "CHANGELOG.rst"]

setup(
    name="core-shared",
    version="1.3.3",
    description="Girl Effect Core Shared",
    long_description="".join(open(filename, "r").read() for filename in LONG_DESCRIPTION_FILES),
    author="Praekelt Consulting",
    author_email="dev@praekelt.com",
    license="BSD",
    url="http://github.com/girleffect/core-shared",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    zip_safe=False,
)
