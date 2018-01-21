#! /usr/bin/env python3

import argparse
from configparser import NoOptionError, NoSectionError
import errno
import hashlib
import logging
import os
import random
import re
import string

import paramiko
from paramiko import SSHClient, sftp_client, ChannelFile
import progressbar as pgb

from shup.config import Config
from shup.error import die

VERBOSE_LEVELV_NUM = 25


def log(message, *args, **kws):
    logging.log(VERBOSE_LEVELV_NUM, message, *args, **kws)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--rule", help="target rule to follow, contains"
                        " everything from host informations to the destination"
                        " folder and the TTL of the file if specified. If not "
                        "specified, shup search for a section 'default' in "
                        "the configuration files",
                        metavar="name", dest="rule", default="default")
    parser.add_argument("file", help="file that should be upload following "
                        "the rule given by the optional `--rule' argument",
                        nargs='+')
    parser.add_argument("-v", "--verbose", help="increase the output "
                        "verbosity during the operation (increase with vv or "
                        "vvv)",
                        action="count", default=0)
    parser.add_argument("-d", "--delwith", help="set the binary used to delete"
                        " the binary when the TTL reach 0",
                        metavar="path", dest="del_bin")
    parser.add_argument("-t", "--ttl", help="set the time while the file will "
                        "stay on the remote host before being deleted",
                        metavar="time", dest="file_ttl")
    parser.add_argument("-p", "--permissions", help="set the file permissions"
                        " in octal mode, default is 0644",
                        metavar="perms", dest="file_perm")
    parser.add_argument("-l", "--file-return", help="set the file return path",
                        metavar="ret", dest="file_return")
    exgroup = parser.add_mutually_exclusive_group()
    exgroup.add_argument("-r", "--randomize", help="randomize filename",
                         action="store_true")
    exgroup.add_argument("-c", help="replace the filename by the file's "
                         "checksum following 'file_cksum' rule in "
                         "configuration files or SHA1 if nothing specified",
                         action="store_true", dest="cksum")
    exgroup.add_argument("--cksum", help="like -c but following the "
                         "command line argument 'algorithm'",
                         metavar="algorithm", dest="file_cksum_arg",
                         choices=hashlib.algorithms_guaranteed)

    return parser.parse_args()


def get_ssh_client(cfg: Config) -> SSHClient:
    '''Return a connected SSHClient'''
    needed_keys = ['ssh_host', 'file_path', 'ssh_port', 'ssh_user']
    miss_keys = [i for i in needed_keys if not cfg.exists(i)]
    if len(miss_keys):
        die(1, "get_ssh_client: missing keys %s in rule '%s'" % (miss_keys,
            cfg.rule))

    s = SSHClient()
    s.load_system_host_keys()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pass_from_file = False
    try:
        passwd = cfg.get_str('ssh_passwd')
        pass_from_file = True
    except NoOptionError:
        passwd = cfg.askPasswd()

    try:
        s.connect(
            cfg.get_str('ssh_host'),
            cfg.get_int('ssh_port'),
            cfg.get_str('ssh_user'),
            passwd,
            timeout=cfg.get_int('ssh_timeout'))
    except paramiko.AuthenticationException as e:
        if pass_from_file:
            print("Please check the password provided in the configuration"
                  " file")
        else:
            print("Wrong password, try again")
            return get_ssh_client(cfg)

    return s


def create_path_then_cd(path: str, sftp: sftp_client):
    '''Create missing directories in provided path and change directory to
    that path'''
    if path == '/':
        sftp.chdir('/')
        return
    if path == '':
        return
    try:
        sftp.chdir(path)
    except IOError:
        dirname, basename = os.path.split(path.rstrip('/'))
        create_path_then_cd(dirname, sftp)
        sftp.mkdir(basename)
        sftp.chdir(basename)
        return True


def get_filename_rnd(cfg: Config):
    '''Return a random file name of length "rand_len".'''
    charset = list(string.ascii_letters + string.digits)
    rand_len = cfg.get_int('rand_len')
    return ''.join([random.choice(charset) for _ in range(rand_len)])


def get_filename_cksum(hash_func: str, fileName: str):
    '''Compute checksum of given file following hash_func algorithm'''
    hash_func = getattr(hashlib, hash_func)()

    log('Calculating file checksum...')
    with open(fileName, "rb") as f:
        for chunk in iter(lambda: f.read(128 * hash_func.block_size), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def get_remote_path(cfg: Config, fpath: str) -> str:
    filename = os.path.basename(fpath)
    if cfg.get_bool("randomize"):
        rnd_name = get_filename_rnd(cfg)
        if '.' in filename:
            filename = "{}.{}".format(rnd_name,
                                      ''.join(filename.split('.', 1)[1]))
        else:
            filename = rnd_name
    elif cfg.get_bool("cksum"):
        if cfg.exists("file_cksum"):
            cksum_name = get_filename_cksum(cfg.get_str("file_cksum"), fpath)
        else:
            cksum_name = get_filename_cksum("sha1", fpath)
        filename = "{}_{}".format(cksum_name, filename)
    elif cfg.exists("file_cksum_arg"):
        cksum_name = get_filename_cksum(cfg.get_str("file_cksum_arg"), fpath)
        filename = "{}_{}".format(cksum_name, filename)

    log("Filename on the host will be: {}".format(filename))

    return os.path.join(cfg.get_str('file_path'), filename)


def log_progress(done, total, bar):
    if not bar[0]:
        widgets = [
                pgb.Percentage(),
                ' ', pgb.Bar(marker='#', left='[', right=']', fill_left=True),
                ' ', pgb.ETA(),
                ' ', pgb.FileTransferSpeed(),
            ]
        bar[0] = pgb.ProgressBar(widgets=widgets, max_value=total).start()
    bar[0].update(done)


def put_file(cfg: Config, sftp: sftp_client, fpath: str, verbose=False) -> str:
    '''Upload the file pointed by the absolute path fpath to the remote host
    that the sftp client connect to'''

    final_path = get_remote_path(cfg, fpath)
    create_path_then_cd(cfg.get_str('file_path'), sftp)

    log('Uploading: {}...'.format(os.path.basename(fpath)))
    if verbose:
        bar = [None]
        try:
            sftp.put(fpath, final_path,
                     callback=lambda x, y: log_progress(x, y, bar))
            if bar[0]:
                bar[0].finish()
        except KeyboardInterrupt:
            logging.warning('Aborded, cleaning remote file')
            sftp.remove(final_path)
            raise KeyboardInterrupt
    else:
        sftp.put(fpath, final_path)

    return final_path


def set_file_mode(sftp: sftp_client, final_path: str, mode: str) -> None:
    log('Changing permissions to {}'.format(mode))

    fmode = int(mode, 8)
    sftp.chmod(final_path, fmode)


def execCmd(ssh_client: SSHClient, cmd: str) -> ChannelFile:
    return ssh_client.exec_command(cmd)


def set_file_owner(cfg: Config, sftp: sftp_client, ssh_client: SSHClient,
                   final_path: str) -> None:
    stdin, stdout, stderr = execCmd(ssh_client, "id -g {}".format(
        cfg.get_str('file_group')))
    stdout = stdout.read()
    gid = int(stdout)
    stdin, stdout, stderr = execCmd(ssh_client, "id -u {}".format(
        cfg.get_str('file_user')))
    stdout = stdout.read()
    uid = int(stdout)
    log('Set file owner to {}:{}'.format(uid, gid))
    sftp.chown(final_path, uid, gid)


def set_delete_time(cfg: Config, ssh_client: SSHClient,
                    final_path: str) -> None:
    del_time = cfg.get_str('file_ttl')
    time_re = re.match('(?P<duration>\d+)(?P<unit>\w?)', del_time)
    cmd = 'echo \'{} "{}"\' | at now + {} {}'
    ttl = {'m': 'minutes',
           'h': 'hours',
           'd': 'days',
           'w': 'weeks',
           'M': 'months',
           }

    if not time_re or time_re.group('unit') not in ttl:
        logging.warn('Invalid time specified, file will not be deleted')
        return

    unit = ttl[time_re.group('unit')]
    log('Set file deletion to now + {} {}'.format(
        time_re.group('duration'), unit))

    cmd = cmd.format(cfg.get_str('del_bin'), final_path,
                     time_re.group('duration'), unit)

    execCmd(ssh_client, cmd)


def main():
    args = get_args()
    logging.addLevelName(VERBOSE_LEVELV_NUM, "VERBOSE")
    if args.verbose == 1:
        logging.basicConfig(level=VERBOSE_LEVELV_NUM)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 2:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    file_paths = map(os.path.abspath, args.file)
    cfg = Config(args)
    log('Connecting to the host...')
    ssh = get_ssh_client(cfg)
    sftp = ssh.open_sftp()
    for local_file in file_paths:
        final_path = put_file(cfg, sftp, local_file, args.verbose)
        set_file_mode(sftp, final_path, cfg.get_str('file_perm'))
        set_file_owner(cfg, sftp, ssh, final_path)
        if (cfg.get_str('file_ttl') != '0'):
            set_delete_time(cfg, ssh, final_path)
        try:
            print(cfg.get_str('file_return') + os.path.basename(final_path))
        except NoOptionError:
            continue
    ssh.close()


if __name__ == '__main__':
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        die(0, "\nInterrupted.")
    except (NoSectionError, NoOptionError) as e:
        die(errno.EINVAL, e.message)
