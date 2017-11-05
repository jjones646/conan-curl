# conan-curl

[Conan](https://conan.io) package for lib cURL library

## Build packages

Download conan and run:

    $ python build.py

## Upload packages to server

    $ conan upload curl/7.56.1@user/channel --all

## Reuse the packages

### Basic setup

    $ conan install curl/7.56.1@user/channel

### Project setup

If you handle multiple dependencies in your project is better to add a *conanfile.txt*

    [requires]
    curl/7.56.1@user/channel

    [options]
    curl:shared=true # false

    [generators]
    txt
    cmake

    [imports]
    ., cacert.pem -> ./bin

Complete the installation of requirements for your project running:</small></span>

    conan install .

Project setup installs the library (and all his dependencies) and generates the files *conanbuildinfo.txt* and *conanbuildinfo.cmake* with all the paths and variables that you need to link with your dependencies.
