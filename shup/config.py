import getpass
from os import path
from os.path import expanduser, dirname
from configparser import ConfigParser


cfg_name = "shup.cfg"
cfg_paths = [
        path.join(dirname(path.realpath(__file__)), cfg_name),
        path.join(expanduser('~/.config/shup'), cfg_name),
        ]


class Config(ConfigParser):

    def __init__(self, arg_parser):
        user = getpass.getuser()
        self.rule = arg_parser.rule
        super().__init__(comment_prefixes=('#', ';'))
        self.read_dict({
            'DEFAULT': {
                'del_bin': 'rm',
                'ssh_port': '22',
                'ssh_timeout': '5',
                'ssh_user': user,
                'file_ttl': '1d',
                'file_perm': '0644',
                'file_group': user,
                'file_user': user,
                'rand_len': '2',
                }})

        for config_path in cfg_paths:
            self.read(config_path)
        args = vars(arg_parser)
        str_args = {}
        for arg in [i for i in args if args[i] is not None]:
            str_args[arg] = str(args[arg])
        self.read_dict({self.rule: str_args})

    def get_str(self, option):
        return super().get(self.rule, option)

    def get_int(self, option):
        return super().getint(self.rule, option)

    def get_bool(self, option):
        return super().getboolean(self.rule, option)

    def exists(self, option):
        return super().has_option(self.rule, option)

    def askPasswd(self):
        return getpass.getpass()
