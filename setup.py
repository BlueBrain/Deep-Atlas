# Copyright 2021, Blue Brain Project, EPFL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The setup script."""
from setuptools import find_packages, setup

install_requires = [
    "numpy",
    "pynrrd",
]

extras_require = {
    "dev": [
        "bandit",
        "black",
        "flake8",
        "flake8-bugbear",
        "flake8-comprehensions",
        "flake8-docstrings",
        "isort",
        "pytest",
        "pytest-cov",
        "tox",
    ],
}

setup(
    name="deepatlas",
    author="Blue Brain Project, EPFL",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require=extras_require,
)
