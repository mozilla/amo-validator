from setuptools import setup, find_packages

from validator import __version__

setup(
    name='amo-validator',
    version=__version__,  # noqa
    description='Validates add-ons for Mozilla products.',
    long_description=open('README.md').read(),
    author='Matt Basta',
    author_email='me@mattbasta.com',
    url='http://github.com/mozilla/amo-validator',
    license='BSD',
    packages=find_packages(exclude=['tests', 'tests/*',
                                    'extras', 'extras/*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[p.strip() for p in open('./requirements.txt') if
                      not p.startswith(('#', '-e'))],
    scripts=["addon-validator"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
