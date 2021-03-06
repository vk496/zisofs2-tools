#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

test_deps = [
    'pytest >= 6.1.1',
]
extras = {
    'test': test_deps,
}

setuptools.setup(
    name="zisofs2-tools-vk496",  # Replace with your own username
    version="0.0.1",
    author="Valentín KIVACHUK BURDÁ",
    author_email="vk18496@gmail.com",
    description="A small example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vk496/zisofs2-tools",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'mkzftree2 = mkzftree2.__main__:main',
        ],
    },
    python_requires='>=3.6',
    install_requires=[
        'lz4 >= 3.1.0',
        'zstandard >= 0.14.0',
        'pywin32 >= 1.0 ; platform_system=="Windows"'
    ],
    tests_require=test_deps,
    extras_require=extras,
)
