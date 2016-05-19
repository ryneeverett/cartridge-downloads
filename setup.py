import setuptools

setuptools.setup(
    name='cartridge-downloads',
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
