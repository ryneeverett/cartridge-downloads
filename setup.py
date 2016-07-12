import setuptools

from cartridge_downloads import __version__

setuptools.setup(
    name='cartridge-downloads',
    description=(
        'Digital product support for the Django/Mezzanine/Cartridge stack.'),
    version=__version__,
    url='https://github.com/ryneeverett/cartridge-downloads',
    author='Ryne Everett',
    author_email='ryneeverett@gmail.com',
    license='BSD',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
    ],
    packages=setuptools.find_packages(),
    install_requires=[
        'cartridge',
        'django-downloadview',
        'django-model-utils',
        'filebrowser_safe==999',
    ],
    dependency_links=[
        'git+https://github.com/ryneeverett/filebrowser-safe.git@downloads#egg=filebrowser_safe-999',
    ],
)
