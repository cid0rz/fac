from fac.commands import Command, Arg
from fac.utils import prompt


class EnvCommand(Command):
    """create and manage set of enabled/disabled mods in different paths
    """

    name = 'env'
    arguments = [
        Arg('action',
            choices=['activate', 'create', 'remove', 'list']),

        Arg('env_name',
            help="environment to operate with",
            nargs='*')
    ]

    def run(self, args):
        if args.action == 'activate':
            self.manager.env_manager.activate_env(args.env_name)
        elif args.action == 'create':
            self.manager.env_manager.create_env(args.env_name)
        elif args.action == 'remove':
            self.manager.env_manager.delete_env(args.env_name)
        elif args.action == 'list':
            self.manager.env_manager.list_envs()

        self.manager.env_manager.save()
