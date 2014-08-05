#
# This file is part of sshoot.

# sshoot is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# sshoot is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with sshoot.  If not, see <http://www.gnu.org/licenses/>.

"""A sshuttle VPN profile."""

import os


class Profile(object):
    """Hold information about a sshuttle profile."""

    _config_attrs = (
        "remote", "subnets", "auto_hosts", "auto_nets", "dns",
        "exclude_subnets", "seed_hosts", "extra_opts")

    remote = None
    subnets = None
    auto_hosts = False
    auto_nets = False
    dns = False
    exclude_subnets = None
    seed_hosts = None
    extra_opts = None

    def __init__(self, subnets):
        self.subnets = subnets

    @classmethod
    def from_dict(cls, config):
        """Create a profile from a dict holding config attributes."""
        config = config.copy()  # shallow, only first-level keys are changed
        try:
            subnets = config.pop("subnets")
        except KeyError:
            raise ProfileError()

        profile = Profile(subnets=subnets)
        for attr in cls._config_attrs:
            value = config.get(attr)
            if value is not None:
                setattr(profile, attr, value)
        return profile

    def cmdline(self, executable="sshuttle", extra_opts=None):
        """Return a sshuttle cmdline based on the profile."""
        cmd = [executable] + self.subnets
        if self.remote:
            cmd.append("--remote={}".format(self.remote))
        if self.auto_hosts:
            cmd.append("--auto-hosts")
        if self.auto_nets:
            cmd.append("--auto-nets")
        if self.dns:
            cmd.append("--dns")
        if self.exclude_subnets:
            cmd.extend(
                "--exclude={}".format(
                    subnet for subnet in self.exclude_subnets.split()))
        if self.seed_hosts:
            cmd.append("--seed-hosts={}".format(",".join(self.seed_hosts)))
        if self.extra_opts:
            cmd.extend(self.extra_opts.split())
        if extra_opts:
            cmd.extend(extra_opts)
        return cmd

    def config(self):
        """Return profile configuration as a dict."""
        conf = {}
        for attr in self._config_attrs:
            value = getattr(self, attr)
            if value:
                conf[attr] = value
        return dict(conf)


class ProfileError(Exception):
    """Profile configuration is not correct."""

    def __init__(self, message="Subnets must be specified"):
        super(ProfileError, self).__init__(message)


def is_profile_running(name, piddir):
    """Return whether the specified profile is running."""
    pidfile = os.path.join(piddir, "{}.pid".format(name))
    try:
        with open(pidfile) as fh:
            pid = int(fh.read())
    except Exception:
        # If anything fails, the pid can't be signalled, so the rofile is not
        # running.
        return False

    try:
        os.kill(pid, 0)
    except OSError:
        # Delete stale pidfile
        os.unlink(pidfile)
        return False
    return True