#!/usr/bin/env python
"""This package contains GRR client templates and components."""
import ConfigParser
import glob
import os
import re
import shutil
from setuptools import setup
from setuptools.command.sdist import sdist

THIS_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

# If you run setup.py from the root GRR dir you get very different results since
# setuptools uses the MANIFEST.in from the root dir.  Make sure we are in the
# package dir.
os.chdir(THIS_DIRECTORY)


def get_config():
  """Get INI parser with version.ini data."""
  ini_path = os.path.join(THIS_DIRECTORY, "version.ini")
  if not os.path.exists(ini_path):
    ini_path = os.path.join(THIS_DIRECTORY, "../../../version.ini")
    if not os.path.exists(ini_path):
      raise RuntimeError("Couldn't find version.ini")

  config = ConfigParser.SafeConfigParser()
  config.read(ini_path)
  return config


VERSION = get_config()


class Sdist(sdist):
  """Make a sdist release."""

  REQUIRED_COMPONENTS = [
      r"grr-chipsec_.+_Linux_CentOS.+i386.bin",
      r"grr-chipsec_.+_Linux_CentOS.+amd64.bin",
      r"grr-chipsec_.+_Linux_debian.+i386.bin",
      r"grr-chipsec_.+_Linux_debian.+amd64.bin",
      r"grr-rekall_.+_Darwin_OSX.+amd64.bin",
      r"grr-rekall_.+_Linux_CentOS.+i386.bin",
      r"grr-rekall_.+_Linux_CentOS.+amd64.bin",
      r"grr-rekall_.+_Linux_debian.+i386.bin",
      r"grr-rekall_.+_Linux_debian.+amd64.bin",
      r"grr-rekall_.+_Windows_7.+amd64.bin",
      r"grr-rekall_.+_Windows_7.+i386.bin",
  ]

  REQUIRED_TEMPLATES = [
      "GRR_maj.minor_amd64.exe.zip",
      "GRR_maj.minor_i386.exe.zip",
      "grr_maj.minor_amd64.deb.zip",
      "grr_maj.minor_amd64.pkg.xar",
      "grr_maj.minor_amd64.rpm.zip",
      "grr_maj.minor_i386.deb.zip",
      "grr_maj.minor_i386.rpm.zip",
  ]

  def CheckTemplates(self, base_dir, version):
    """Verify we have at least one template that matches maj.minor version."""
    major_minor = ".".join(version.split(".")[0:2])
    templates = glob.glob(os.path.join(base_dir, "templates/*%s*.zip" %
                                       major_minor))
    templates.extend(glob.glob(os.path.join(base_dir, "templates/*%s*.xar" %
                                            major_minor)))

    required_templates = set([x.replace("maj.minor", major_minor)
                              for x in self.REQUIRED_TEMPLATES])

    # Client templates have an extra version digit, e.g. 3.1.0.0
    templates_present = set([
        re.sub(r"_%s[^_]+_" % major_minor, "_%s_" % major_minor,
               os.path.basename(x)) for x in templates
    ])

    difference = required_templates - templates_present
    if difference:
      raise RuntimeError("Missing templates %s" % difference)

  def CheckComponents(self, base_dir):
    """Verify we have components for each supported system."""
    components = [os.path.basename(x)
                  for x in glob.glob(os.path.join(base_dir, "components/*.bin"))
                 ]
    missing = set()
    for requirement in self.REQUIRED_COMPONENTS:
      for component in components:
        if re.match(requirement, component):
          break
      else:
        missing.add(requirement)
    if missing:
      raise RuntimeError("Missing components: %s" % missing)

  def run(self):
    base_dir = os.getcwd()
    self.CheckTemplates(base_dir, setup_args["version"])
    self.CheckComponents(base_dir)
    sdist.run(self)
    print "To upload a release, run upload.sh [version]"

  def make_release_tree(self, base_dir, files):
    sdist.make_release_tree(self, base_dir, files)
    sdist_version_ini = os.path.join(base_dir, "version.ini")
    if os.path.exists(sdist_version_ini):
      os.unlink(sdist_version_ini)
    shutil.copy(
        os.path.join(THIS_DIRECTORY, "../../../version.ini"), sdist_version_ini)


def find_data_files(source, prefix=None):
  result = []
  for directory, _, files in os.walk(source):
    files = [os.path.join(directory, x) for x in files]
    if prefix:
      result.append((os.path.join(prefix, directory), files))
    else:
      result.append((directory, files))

  return result


if "VIRTUAL_ENV" not in os.environ:
  print "*****************************************************"
  print "  WARNING: You are not installing in a virtual"
  print "  environment. This configuration is not supported!!!"
  print "  Expect breakage."
  print "*****************************************************"

setup_args = dict(
    name="grr-response-templates",
    version=VERSION.get("Version", "packageversion"),
    description="GRR Rapid Response client templates and components.",
    long_description=("This PyPi package is just a placeholder. The package"
                      " itself is too large to distribute on PyPi so it is "
                      "available from google cloud storage. See"
                      " https://github.com/google/grr-doc/blob/master/"
                      "installfrompip.adoc for installation instructions."),
    license="Apache License, Version 2.0",
    url="https://github.com/google/grr",
    data_files=(find_data_files(
        "components", prefix="grr-response-templates") + find_data_files(
            "templates", prefix="grr-response-templates") + ["version.ini"]),
    cmdclass={
        "sdist": Sdist,
    })

setup(**setup_args)
