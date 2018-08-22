from setuptools import setup, find_packages


with open("README.md", "r") as fh:
	long_description = fh.read()


setup(
	name="FlexKit",
	version="0.0.0",
	author="David Kyalo",
	author_email="davidmkyalo@gmail.com",
	description="Application framework",
	long_description=long_description,
	# long_description_content_type="text/markdown",
	url="https://github.com/centergy/flex",
	packages=find_packages(include=['flex.*']),
	install_requires=[
		'Werkzeug', 'Blinker'
	],
	classifiers=(
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	),
)