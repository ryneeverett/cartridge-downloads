import setuptools

setuptools.setup(
    name='cartridge-downloads',
    description=(
        'Digital product support for the Django/Mezzanine/Cartridge stack.'),
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

        # 0.4.4 -- FileBrowseField's now return a FileField which is necessary
        # for django-downloadview.See
        # https://github.com/stephenmcd/filebrowser-safe/pull/77.
        'filebrowser_safe>=0.4.4',
    ],
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    include_package_data=True,
)
