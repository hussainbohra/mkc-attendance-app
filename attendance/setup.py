#!/usr/bin/env python
import setuptools
import os
import src.attendance.version as mod_version


def version():
    base_version = mod_version.__version__

    # Add build number
    if os.environ.get('BLD_NUMBER'):
        build = os.environ.get('BLD_NUMBER')
    elif os.environ.get('BUILD_NUMBER'):
        build = os.environ.get('BUILD_NUMBER')
    else:
        build = "0"
    version = base_version + "." + build

    # Add branch suffix
    if os.environ.get('BLD_BRANCH') == 'master':
        return version
    elif os.environ.get('BLD_BRANCH_SUFFIX') and os.environ.get('BLD_NUMBER'):
        version += os.environ.get('BLD_BRANCH_SUFFIX')
    else:
        version += '-local'

    return version


setuptools.setup(
    name="mkc-attendance-app",
    version=version(),
    author="Hussain Bohra",
    author_email="hussainbohra@gmail.com",
    description="[MKC] Attendance App",
    packages=setuptools.find_packages(
        "src", include=["attendance", "attendance*"]),
    package_dir={"": "src"},
    scripts=[],
    install_requires=[
        'configobj',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'pandas',
        'structlog',
    ],
    test_requires=[],
    test_suite="tests",
    license='Proprietary',
    classifiers=(
        "Programming Language :: Python :: 3.6",
    )
)
