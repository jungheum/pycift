"""setup.py for pycift

"""

import sys
from setuptools import setup


install_requires = [
    'selenium',
    'python-dateutil',
    'requests',
    'construct',
    'peewee<3',
    'iso8601'
]

if sys.platform == "win32":
    install_requires.append('pypiwin32')
else:
    install_requires.append('pyvirtualdisplay')


setup(
    name="pycift",
    version="1.0.20180318",
    packages=["pycift",
              "pycift.acquisition",
              "pycift.report",
              "pycift.utility"],
    author="Hyunji Chung",
    author_email="localchung@gmail.com",
    url="https://bitbucket.org/cift/pycift",
    description="A Python implementation of CIFT (Cloud-based IoT Forensic Toolkit)",
    long_description=open('README.md').read(),
    license=open('LICENSE').read(),
    zip_safe=False,
    install_requires=install_requires,
    platforms=['win', 'linux'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Researchers',
        'Intended Audience :: Developers',
        'Intended Audience :: Educators',
        'Intended Audience :: Investigators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Microsoft',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.x',
        'Topic :: Digital Forensics',
        'Topic :: Security',
        'Topic :: Cloud-based IoT Forensics',
        'Topic :: Client Centric Artifacts',
        'Topic :: Cloud Native Artifacts',
        'Topic :: Intelligent Virtual Assistant'
    ],
)
