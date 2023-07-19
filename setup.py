from setuptools import setup, find_packages

requirements = open('./requirements.txt', 'r').read().split("\n")

setup(
    name='commons-falcon',
    packages=[
        'commons_falcon', 
        'commons_falcon.middlewares', 
        'commons_falcon.errors', 
        'commons_falcon.csv', 
        'commons_falcon.routes',
        'commons_falcon.hooks',
        'commons_falcon.hooks.mongo',
        'commons_falcon.response',
        'commons_falcon.mixins'
    ],
    version='1.0.0',
    author="Develper Junio",
    author_email='developer@junio.in',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    description="Falcon Utilities, Middlewares, Error Classes",
    license="MIT license",
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "elasticsearch>=7.14.0",
        "flatten-json>=0.1.13",
        "six>=1.16.0",
        "falcon-caching>=1.1.0",
        "limits>=2.7.0",
        "stringcase>=1.2.0",
        "jwcrypto>=1.4.2",
    ]
)