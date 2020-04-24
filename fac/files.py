import os
import sys
import json
import os.path

from configparser import ConfigParser

from appdirs import user_config_dir, user_data_dir

from fac.utils import JSONDict, Version, prompt

__all__ = ['Config', 'EnvConfig', 'JSONFile']

FACTORIO_SEARCH_PATHS = [
    '.',
    os.path.join('.', 'factorio'),
    os.path.join('.', 'Factorio'),
    '..',
    os.path.join('..', 'factorio'),
    os.path.join('..', 'Factorio'),
    user_data_dir('factorio', appauthor=False),
    user_data_dir('Factorio', appauthor=False),
    os.path.join(
        user_data_dir('Steam', appauthor=False),
        os.path.join('SteamApps', 'common', 'Factorio'),
    ),
    os.path.join(
        user_data_dir('Steam', appauthor=False),
        os.path.join('steamapps', 'common', 'Factorio'),
    ),
]

if sys.platform.startswith('win32'):
    FACTORIO_SEARCH_PATHS += [
        r'%APPDATA%\factorio',
        r'C:\Program Files (x86)\Steam\SteamApps\common\factorio',
    ]
elif sys.platform.startswith('linux'):
    FACTORIO_SEARCH_PATHS += [
        '~/factorio',
        '~/Factorio',
        '~/.factorio',
        '/usr/share/factorio/',
    ]
else:
    FACTORIO_SEARCH_PATHS += [
        '~/factorio',
        '~/Factorio',
        '~/.factorio',
        '/Applications/factorio.app/Contents',
        os.path.join(
            user_data_dir('Steam', appauthor=False),
            os.path.join('SteamApps', 'common', 'Factorio',
                         'factorio.app', 'Contents'),
        ),
        os.path.join(
            user_data_dir('Steam', appauthor=False),
            os.path.join('steamapps', 'common', 'Factorio',
                         'factorio.app', 'Contents'),
        ),
    ]


class Config(ConfigParser):
    default_config = '''
    [mods]
    hold =

    [paths]
    data-path =
    write-path =

    [db]
    update_period = 600
    '''

    def __init__(self, config_file=None):
        super().__init__(allow_no_value=True)

        self.read_string(self.default_config)
        self.hold = []
        self.forced_game_version = None
        self.forced_mods_directory = None
        if config_file:
            self.config_file = config_file
        else:
            self.config_file = os.path.join(
                user_config_dir('fac', appauthor=False),
                'config.ini'
            )

        if os.path.isfile(self.config_file):
            self.load()

    def load(self):
        self.read(self.config_file)
        self.hold = self.get('mods', 'hold').split()
        dirname = os.path.dirname(self.config_file)

    def save(self):
        dirname = os.path.dirname(self.config_file)

        hold = '\n'.join(self.hold)
        self.set('mods', 'hold', hold)

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.write(f)

    @staticmethod
    def is_factorio_data_path(path):
        return os.path.isfile(os.path.join(path, 'base', 'info.json'))

    @staticmethod
    def is_factorio_write_path(path):
        config_dir = os.path.join(path, 'config')
        mods_dir = os.path.join(path, 'mods')
        if not (os.path.isdir(config_dir) and
                os.path.isdir(mods_dir)):
            return False

        if not (os.access(config_dir, os.W_OK) and
                os.access(mods_dir, os.W_OK)):
            return False
        return True

    @property
    def factorio_data_path(self):
        path = self.get('paths', 'data-path')

        if path and self.is_factorio_data_path(path):
            return path
        elif path:
            raise Exception(
                "The supplied data path (%s) does not seem to be correct.\n"
                "Please check the data-path variable in %s and make sure it "
                "points to a data directory containing a base/info.json file."
                % (path, self.config_file)
            )
        else:
            for path in FACTORIO_SEARCH_PATHS:
                path = os.path.expanduser(path)
                path = os.path.expandvars(path)
                if self.is_factorio_data_path(path):
                    return path
                path = os.path.join(path, 'data')
                if self.is_factorio_data_path(path):
                    return path

        raise Exception(
            "Can not find the factorio data path.\n"
            "Please set the data-path variable in %s" % (
                self.config_file
            )
        )

    @property
    def factorio_write_path(self):
        path = self.get('paths', 'write-path')

        if path and self.is_factorio_write_path(path):
            return path
        elif path:
            raise Exception(
                "The supplied write path (%s) does not seem to be correct.\n"
                "Please check the write-path variable in %s and make sure it "
                "points to a directory containing writeable 'config' and "
                "'mods' subdirectories." % (
                    path,
                    self.config_file,
                )
            )
        else:
            for path in FACTORIO_SEARCH_PATHS:
                path = os.path.expanduser(path)
                path = os.path.expandvars(path)
                if self.is_factorio_write_path(path):
                    return path

        raise Exception(
            "Can not find a valid factorio write path.\n"
            "Please set one using the write-path variable in %s" % (
                self.config_file
            )
        )

    @property
    def player_data(self):
        return JSONFile(
            os.path.join(
                self.factorio_write_path,
                'player-data.json'
            )
        )

    def get_game_version(self):
        if self.forced_game_version:
            return self.forced_game_version

        json_file = os.path.join(
            self.factorio_data_path,
            'base', 'info.json'
        )
        json = JSONFile(json_file)
        return json.version

    def set_game_version(self, version):
        self.forced_game_version = version

    game_version = property(get_game_version, set_game_version)

    @property
    def game_version_major(self):
        return Version('.'.join(self.game_version.split('.')[:2]))

    def get_mods_directory(self):
        if self.forced_mods_directory:
            return self.forced_mods_directory
        return os.path.join(self.factorio_write_path, 'mods')

    def set_mods_directory(self, directory):
        self.forced_mods_directory = directory

    mods_directory = property(get_mods_directory, set_mods_directory)


class EnvConfig(ConfigParser):
    '''Helper class to manage different environments. It will be called from Config object and there will be a default configuration with a default environment called 'default'. The format of the file is:

    [env_name1]
    data-path =
    write-path =
    disabled =
    held =

    [env_name2]
    data-path =
    write-path =
    disabled =
    held =

    .
    .
    .

    [env_nameN]
    data-path =
    write-path =
    disabled =
    held =


    [A000] #This is a special tag for the active envirnoment
    active = default
    '''

    default_config = '''
    [A000]
    active = default
    [default]
    data-path = {}
    write-path = {}
    disabled = {}
    held = {}
    '''

    def __init__(self, env_file=None, config=None, manager=None):
        super().__init__(allow_no_value=True)

        self.conf = config
        self.manager = manager
        self.active = None

        if env_file:
            self.env_file = env_file
        else:
            self.env_file = os.path.join(user_config_dir(
                'fac', appauthor=False), 'envs.conf')
            print("creating a envs config file for fac envirnoments in\n{}\n \
                  with current environment as 'default'".format(self.env_file))
            mods = self.manager.find_mods()
            dis = [mod for mod in mods if not self.manager.is_mod_enabled(mod)]
            held = self.conf.hold
            with open(self.env_file, 'w') as f:
                print(self.default_config.format(
                    self.conf.factorio_data_path, self.conf.factorio_write_path, dis, held), file=f)
            with open(os.path.join(user_config_dir('fac', appauthor=False), 'test'), 'w') as f:
                print(self.default_config.format(
                    self.conf.factorio_data_path, self.conf.factorio_write_path, dis, held), file=f)

    def load(self):
        self.read(self.env_file)
        self.active = self.get('A000', 'active')
        self.remove_section('A000')
        self.activate_env([self.active])

    def save(self):
        dirname=os.path.dirname(self.env_file)
        self.add_section('A000')
        self.set('A000', 'active', str(self.active))

        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(self.env_file, 'w') as f:
            self.write(f)

    def activate_env(self, name):
        name=name[0]
        if name not in self.sections():
            print('env {} not found'.format(name))
        else:
            print('activating env {}'.format(name))
            data=self.get(name, 'data-path')
            if not self.conf.is_factorio_data_path(data):
                print('wrong data path {} on environment {}'.format(data, name))
                return
            else:
                self.conf.data_path=data

            write = self.get(name, 'write-path')
            if not self.conf.is_factorio_write_path(write):
                print('wrong  path {} on environment {}'.format(data, name))
                return
            else:
                self.conf.write_path = write

            dis = self.get(name, 'disabled')
            dis = [mod.strip().strip("'")
                   for mod in dis.strip('[]').split(',')]
            dis = [mod.strip("'") for mod in dis]
            for mod in dis:
                if mod in [installed.name for installed in self.manager.find_mods()]:
                    self.manager.set_mod_enabled(mod, enabled=False)
                    print('{} has been disabled'.format(mod))
                else:
                    print('{} is not installed so cannot be disabled'.format(mod))
            for mod in [installed.name for installed in self.manager.find_mods()]:
                if mod not in dis:
                    self.manager.set_mod_enabled(mod, enabled=True)
                    print('{} has been enabled'.format(mod))

            held = self.get(name, 'held')
            held = [mod.strip().strip("'")
                    for mod in held.strip('[]').split(',')]
            self.conf.hold = held
            print('mods held : {}'.format(self.conf.hold))
        self.active = name

    def create_env(self, name):
        name = str(name[0])
        if name not in self.sections():
            self.add_section(name)
            print('creating env {}'.format(name))
        elif not prompt(prompt='Overwrite env {}?'.format(name)):
            print('aborting overwrite on env {}'.format(name))
            return
        else:
            print('overwriting env {}'.format(name))

        self.set(name, 'data-path', self.conf.factorio_data_path)
        self.set(name, 'write-path', self.conf.factorio_write_path)
        mods = self.manager.find_mods()
        dis = [
            mod.name for mod in mods if not self.manager.is_mod_enabled(mod.name)]
        self.set(name, 'disabled', str(dis))
        held = self.conf.hold
        self.set(name, 'held', str(held))

    def save_env(self, name=None):
        if name:
            name = name[0]
        else:
            name = self.active

        if name not in self.sections():
            print('error trying to save env {}'.format(name))
        else:
            self.set(name, 'data-path', self.conf.factorio_data_path)
            self.set(name, 'write-path', self.conf.factorio_write_path)
            mods = self.manager.find_mods()
            dis = [
                mod.name for mod in mods if not self.manager.is_mod_enabled(mod.name)]
            self.set(name, 'disabled', str(dis))
            held = self.conf.hold
            self.set(name, 'held', str(held))

    def delete_env(self, name):
        if name == 'default':
            print('cannot delete default env')
            return
        name = name[0]
        if name not in self.sections():
            print('env {0} not found'.format(name))
        else:
            print('removing {}  '.format(name))
            self.remove_section(name)

    def list_envs(self):
        print('\nlist of environments:')
        for env in self.sections():
            print(env)
            for opt in self.options(env):
                print('    {:12} {} '.format(opt+':', self.get(env, opt)))
            print()
        return


class JSONFile(JSONDict):
    file = None

    def __init__(self, file):
        self.file = file
        self.data = {}
        self.reload()

    def __enter__(self):
        return self

    def __exit__(self):
        self.save()

    def reload(self):
        if not os.path.exists(self.file):
            return

        with open(self.file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def save(self):
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    @property
    def mtime(self):
        try:
            return os.path.getmtime(self.file)
        except IOError:
            return 0

    def utime(self, *args, **kwargs):
        os.utime(self.file, *args, **kwargs)
