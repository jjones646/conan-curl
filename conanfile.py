import os
import conans
import semver

from conans import tools, CMake, ConanFile, AutoToolsBuildEnvironment
from conans.tools import download, unzip, replace_in_file, check_sha256

# fail if using an old version of conan
required_conan_version = '0.28.0'
assert semver.gte(conans.__version__, required_conan_version, loose=True), 'Not compatible with Conan version {!s}. You must use Conan version {!s} or greater.'.format(conans.__version__, required_conan_version)


class CurlConan(ConanFile):
    name = 'curl'
    version = '7.56.1'
    url = 'https://github.com/jjones646/conan-curl'
    license = 'https://curl.haxx.se/docs/copyright.html'
    settings = 'os', 'arch', 'compiler', 'build_type'
    options = {
        'shared': [True, False],  # SHARED IN LINUX IS HAVING PROBLEMS WITH LIBEFENCE
        'with_openssl': [True, False],
        'with_ldap': [True, False],
        'custom_cacert': [True, False],
        'darwin_ssl': [True, False],
        'with_libssh2': [True, False],
        'with_libidn': [True, False],
        'with_librtmp': [True, False],
        'with_libmetalink': [True, False]
    }
    default_options = 'shared=False', 'with_openssl=True', 'with_ldap=False', \
                      'custom_cacert=False', 'darwin_ssl=True', 'with_libssh2=False', \
                      'with_libidn=False', 'with_librtmp=False', 'with_libmetalink=False'
    build_requires = 'zlib/[~=1.2]@jjones646/stable'
    exports = ['CMakeLists.txt', 'FindCURL.cmake']
    generators = 'cmake', 'txt'
    short_paths = True

    def config_options(self):
        if self.options.with_openssl:
            if self.settings.os != 'Macos' or not self.options.darwin_ssl:
                self.options['OpenSSL'].shared = self.options.shared
        if self.settings.os != 'Macos':
            try:
                self.options.remove('darwin_ssl')
            except Exception:
                pass

    def configure(self):
        if self.options.with_openssl:
            if self.settings.os != 'Macos' or not self.options.darwin_ssl:
                self.requires.add('OpenSSL/[~=1.0.2-]@jjones646/stable', private=False)

    @property
    def _archive_dirname(self):
        return 'curl'

    def source(self):
        archive_dirname = '{!s}-{!s}'.format(self._archive_dirname, self.version)
        archive_filename = '{!s}.tar.gz'.format(archive_dirname)
        download_url = 'https://curl.haxx.se/download/{!s}'.format(archive_filename)
        download(download_url, archive_filename, verify=False)
        check_sha256(archive_filename, '961a25531d72a843dfcce87b290e7a882f2d376f3b88de11df009710019c5b16')
        unzip(archive_filename)
        os.unlink(archive_filename)
        os.rename(archive_dirname, 'curl')

        download('https://curl.haxx.se/ca/cacert.pem', 'cacert.pem', verify=False)
        if self.settings.os != 'Windows':
            self.run('chmod +x ./{!s}/configure'.format(self._archive_dirname))

    def build(self):
        if self.settings.os == 'Linux' or self.settings.os == 'Macos':
            suffix = ' --without-libidn ' if not self.options.with_libidn else '--with-libidn'
            suffix += ' --without-libssh2 ' if not self.options.with_libssh2 else '--with-libssh2'
            suffix += ' --without-librtmp ' if not self.options.with_librtmp else '--with-librtmp'
            suffix += ' --without-libmetalink ' if not self.options.with_libmetalink else '--with-libmetalink'

            if self.options.with_openssl:
                if self.settings.os == 'Macos' and self.options.darwin_ssl:
                    suffix += '--with-darwinssl '
                else:
                    suffix += '--with-ssl '
            else:
                suffix += '--without-ssl '

            suffix += '--with-zlib={!s} '.format(self.deps_cpp_info['zlib'].lib_paths[0])

            if not self.options.shared:
                suffix += ' --disable-shared'
            if not self.options.with_ldap:
                suffix += ' --disable-ldap'
            if self.options.custom_cacert:
                suffix += ' --with-ca-bundle=cacert.pem'

            env_build = AutoToolsBuildEnvironment(self)
            # Hack for configure, don't know why fails because it's not able to find libefence.so
            if 'efence' in env_build.libs:
                env_build.libs.remove('efence')

            with tools.environment_append(env_build.vars):
                with tools.chdir(self._archive_dirname):
                    replace_in_file('./configure', r'-install_name \$rpath/', '-install_name ')
                    configure = './configure {!s}'.format(suffix)
                    self.output.warn(configure)
                    self.run(configure)
                    self.run('make')

        else:
            # Do not compile curl tool, just library
            conan_magic_lines = '''project(CURL)
cmake_minimum_required(VERSION 3.0)
include(../conanbuildinfo.cmake)
CONAN_BASIC_SETUP()
'''
            replace_in_file('{!s}/CMakeLists.txt'.format(self._archive_dirname), 'cmake_minimum_required(VERSION 2.8 FATAL_ERROR)', conan_magic_lines)
            replace_in_file('{!s}/CMakeLists.txt'.format(self._archive_dirname), 'project( CURL C )', '')
            replace_in_file('{!s}/CMakeLists.txt'.format(self._archive_dirname), 'include(CurlSymbolHiding)', '')

            replace_in_file('{!s}/src/CMakeLists.txt'.format(self._archive_dirname), 'add_executable(', 'IF(0)\n add_executable(')
            replace_in_file('{!s}/src/CMakeLists.txt'.format(self._archive_dirname), 'install(TARGETS ${EXE_NAME} DESTINATION bin)', 'ENDIF()')  # EOF

            cmake = CMake(self.settings)
            static = '-DCURL_STATICLIB=OFF' if self.options.shared else '-DCURL_STATICLIB=ON'
            ldap = '-DCURL_DISABLE_LDAP=ON' if not self.options.with_ldap else '-DCURL_DISABLE_LDAP=OFF'

            self.run('cd {!s} && mkdir _build'.format(self._archive_dirname))
            cd_build = 'cd {!s}/_build'.format(self._archive_dirname)
            self.run('{!s} && cmake .. {!s} -DBUILD_TESTING=OFF {!s} {!s}'.format(cd_build, cmake.command_line, ldap, static))
            self.run('{!s} && cmake --build . {!s}'.format(cd_build, cmake.build_config))

    def package(self):
        # Copy findZLIB.cmake to package
        self.copy('FindCURL.cmake', '.', '.')
        # Copying zlib.h, zutil.h, zconf.h
        self.copy('*.h', 'include/curl', '{!s}'.format(self._archive_dirname), keep_path=False)
        # Copy the certs to be used by client
        self.copy(pattern='cacert.pem', keep_path=False)
        # Copying static and dynamic libs
        if self.settings.os == 'Windows':
            if self.options.shared:
                self.copy(pattern='*.dll', dst='bin', src=self._archive_dirname, keep_path=False)
            self.copy(pattern='*.lib', dst='lib', src=self._archive_dirname, keep_path=False)
        else:
            if self.options.shared:
                if self.settings.os == 'Macos':
                    self.copy(pattern='*.dylib', dst='lib', keep_path=False, links=True)
                else:
                    self.copy(pattern='*.so*', dst='lib', src=self._archive_dirname, keep_path=False, links=True)
            else:
                self.copy(pattern='*.a', dst='lib', src=self._archive_dirname, keep_path=False, links=True)

    def package_info(self):
        if self.settings.os != 'Windows':
            self.cpp_info.libs = ['curl']
            self.cpp_info.libs.extend(['pthread'])
            if self.settings.os == 'Linux':
                self.cpp_info.libs.extend(['rt'])
                if self.options.with_libssh2:
                    self.cpp_info.libs.extend(['ssh2'])
                if self.options.with_libidn:
                    self.cpp_info.libs.extend(['idn'])
                if self.options.with_librtmp:
                    self.cpp_info.libs.extend(['rtmp'])
            if self.settings.os == 'Macos':
                if self.options.with_ldap:
                    self.cpp_info.libs.extend(['ldap'])
                if self.options.darwin_ssl:
                    # self.cpp_info.libs.extend(['/System/Library/Frameworks/Cocoa.framework', '/System/Library/Frameworks/Security.framework'])
                    self.cpp_info.exelinkflags.append('-framework Cocoa')
                    self.cpp_info.exelinkflags.append('-framework Security')
                    self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
        else:
            self.cpp_info.libs = ['libcurl_imp'] if self.options.shared else ['libcurl']
            self.cpp_info.libs.append('Ws2_32')
            if self.options.with_ldap:
                self.cpp_info.libs.append('wldap32')
        if not self.options.shared:
            self.cpp_info.defines.append('CURL_STATICLIB=1')
