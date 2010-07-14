from setuptools import setup, find_packages


setup(
    name='amo-validator',
    version='1.0',
    description='Validates addons for Mozilla products.',
    long_description=open('README.rst').read(),
    author='Matt Basta',
    author_email='me@mattbasta.com',
    url='http://github.com/mattbasta/amo-validator',
    license='BSD',
    packages=find_packages(exclude=['tests',
                                    'tests/*',
                                    'extras',
                                    'extras/*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=['nose',
                      'cssutils',
                      'rdflib'],
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
