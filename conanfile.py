import subprocess
import os

from conans import ConanFile, CMake, tools

class Sqlpp11connectorpostgresqlConan(ConanFile):
    name = "sqlpp11-connector-postgresql"
    version = "latest"
    license = "MIT"
    url = "https://github.com/ZaMaZaN4iK/conan-sqlpp11-connector-postgresql"
    description = "A connector for sqlpp11 library."
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False] }
    default_options = "shared=False"
    generators = "cmake"
    requires = (
        "sqlpp11/0.57@bincrafters/stable",
        "boost/1.72.0") # Change in a future to Boost.Lexical_Cast/1.66.0@bincrafters/stable # Boost/1.64.0@bincrafters/stable

    def getPostgreSQLIncludeDir(self):
        return subprocess.check_output(r"pg_config --includedir | tr -d '\n'", shell=True)

    def getPostgreSQLLibDir(self):
        return subprocess.check_output(r"pg_config --libdir | tr -d '\n'", shell=True)
    
    def source(self):
        self.run("git clone https://github.com/matthijs/sqlpp11-connector-postgresql.git")
        with tools.chdir("sqlpp11-connector-postgresql"):
            self.run("git checkout master") # TODO update to version checkout
            # This small hack might be useful to guarantee proper /MT /MD linkage in MSVC
            # if the packaged project doesn't have variables to set it properly
            tools.replace_in_file("CMakeLists.txt", "project(sqlpp11-connector-postgresql VERSION 0.1 LANGUAGES CXX)", '''project(sqlpp11-connector-postgresql VERSION 0.1 LANGUAGES CXX)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()''')

    def build(self):
        cmake = CMake(self)
        if self.settings.os == "Windows":
            pg_root = os.getenv("PostgreSQL_ROOT")
            if not pg_root:
                raise ValueError('PostgreSQL_ROOT must be set in the environment variables.')
            cmake.definitions["POSTGRESQL_ROOT_DIR"] = pg_root
        else:
            cmake.definitions["PostgreSQL_ROOT_DIRECTORIES"] = "%s %s" % (self.getPostgreSQLIncludeDir(), self.getPostgreSQLLibDir())
        cmake.definitions["sqlpp11_ROOT_DIR"] = self.deps_cpp_info["sqlpp11"].rootpath
        cmake.definitions["CMAKE_MODULE_PATH"] = ("%s;%s/lib/cmake/Sqlpp11" % (cmake.definitions.get("CMAKE_MODULE_PATH", ""), self.deps_cpp_info["sqlpp11"].rootpath)).replace('\\', '/')
        cmake.definitions["CMAKE_PREFIX_PATH"] = "%s/lib/cmake/Sqlpp11" % self.deps_cpp_info["sqlpp11"].rootpath
        cmake.configure(source_folder="sqlpp11-connector-postgresql")
        cmake.definitions["ENABLE_TESTS"] = False
        cmake.definitions["CODE_COVERAGE"] = False
        cmake.build()

        # Explicit way:
        # self.run('cmake %s/hello %s' % (self.source_folder, cmake.command_line))
        # self.run("cmake --build . %s" % cmake.build_config)

    def package(self):
        self.copy("*.h", dst="include", src="sqlpp11-connector-postgresql/include")
        self.copy("*.py", dst="scripts", src="sqlpp11-connector-postgresql/scripts", keep_path=False)
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        if self.options.shared == "True":
            self.cpp_info.libs = ["sqlpp11-connector-postgresql-dynamic"]
        else:
            self.cpp_info.libs = ['sqlpp11-connector-postgresql']

        self.user_info.DDL2CPP = os.path.join(self.package_folder, "scripts", "ddl2cpp.py")
