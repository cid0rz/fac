from fac.commands import Command, Arg
from fac.errors import ModNotFoundError


class EnableDisableCommand(Command):
    arguments = [
        Arg('mods', nargs='+', help="mods patterns to affect"),
    ]

    def run(self, args):
        enabled = self.name == 'enable'

        for mod_pattern in args.mods:
            try:
                mod_name = self.manager.resolve_mod_name(mod_pattern)
            except ModNotFoundError as e:
                print("Error: %s" % e)
                continue

            mods = self.manager.find_mods(mod_name)

            if not mods:
                print("No match found for %s" % mod_pattern)
                continue

            for mod in mods:
                if not self.manager.set_mod_enabled(mod.name, enabled):
                    print("%s was already %sd" % (mod.name, self.name))
                else:
                    print("%s is now %sd" % (mod.name, self.name))

        self.manager.env_manager2.save_env()


class EnableCommand(EnableDisableCommand):
    """Enable mods."""

    name = 'enable'


class DisableCommand(EnableDisableCommand):
    """Disable mods."""

    name = 'disable'
