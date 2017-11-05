import os

from conans.model.conan_file import ConanFile
from conans import CMake


class CurlConanTestPackage(ConanFile):
    version = '0.0.0'
    settings = 'os', 'compiler', 'arch', 'build_type'
    generators = 'cmake'

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy(pattern='*.dll', dst='bin', src='bin')
        self.copy(pattern='*.dylib', dst='bin', src='lib')
        self.copy(pattern='*cacert*', dst='bin')

    def test(self):
        self.run('cd bin && .{!s}CurlPackageTest'.format(os.sep))
