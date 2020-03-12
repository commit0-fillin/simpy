# encoding: utf-8
from setuptools import setup, find_packages


setup(
    name='simpy',
    version='3.0.11',
    author='Ontje Lünsdorf, Stefan Scherfke',
    author_email='the_com@gmx.de, stefan@sofa-rockers.org',
    description='Event discrete, process based simulation for Python.',
    long_description='\n\n'.join(
        open(f, 'rb').read().decode('utf-8')
        for f in ['README.rst', 'CHANGES.rst', 'AUTHORS.rst']),
    url='https://simpy.readthedocs.io',
    license='MIT License',
    install_requires=[],
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Scientific/Engineering',
    ],
)
