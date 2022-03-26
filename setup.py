# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in angola_erp_ocr/__init__.py
from angola_erp_ocr import __version__ as version

setup(
	name="angola_erp_ocr",
	version=version,
	description="OCR PDF or Image Files...",
	author="Helio de Jesus",
	author_email="hcesar@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
