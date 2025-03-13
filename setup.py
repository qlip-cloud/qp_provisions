from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in qp_provisions/__init__.py
from qp_provisions import __version__ as version

setup(
	name='qp_provisions',
	version=version,
	description='Provisions Config5',
	author='H&[D[3}[D[}}}}}}}}}}}}}}}}}}}}}}}[B[B[B[B[B',
	author_email='h6enderson037g5mail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
