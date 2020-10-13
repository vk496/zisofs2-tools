#!/usr/bin/env python3
'''
passthroughfs.py - Example file system for pyfuse3

This file system mirrors the contents of a specified directory tree.

Caveats:

 * Inode generation numbers are not passed through but set to zero.

 * Block size (st_blksize) and number of allocated blocks (st_blocks) are not
   passed through.

 * Performance for large directories is not good, because the directory
   is always read completely.

 * There may be a way to break-out of the directory tree.

 * The readdir implementation is not fully POSIX compliant. If a directory
   contains hardlinks and is modified during a readdir call, readdir()
   may return some of the hardlinked files twice or omit them completely.

 * If you delete or rename files in the underlying file system, the
   passthrough file system will get confused.

Copyright ©  Nikolaus Rath <Nikolaus.org>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import faulthandler
from mkzftree2.utils import NotCompressedFile
from mkzftree2.models.FileObject import FileObject
import math
from collections import deque
import trio
from collections import defaultdict
from os import fsencode, fsdecode
from pyfuse3 import FUSEError
import stat as stat_m
import logging
import errno
from argparse import ArgumentParser
import pyfuse3
import os
import sys

# If we are running from the pyfuse3 source directory, try
# to load the module from there first.
basedir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..'))
if (os.path.exists(os.path.join(basedir, 'setup.py')) and
        os.path.exists(os.path.join(basedir, 'src', 'pyfuse3.pyx'))):
    sys.path.insert(0, os.path.join(basedir, 'src'))


faulthandler.enable()

log = logging.getLogger(__name__)


class Operations(pyfuse3.Operations):

    enable_writeback_cache = True

    def __init__(self, source):
        super().__init__()
        self._inode_path_map = {pyfuse3.ROOT_INODE: source}
        self._lookup_cnt = defaultdict(lambda: 0)
        self._fd_inode_map = dict()
        self._inode_fd_map = dict()
        self._fd_open_count = dict()

        self._fileobject_map = dict()
        self._fileobject_path_map = dict()

        self._blockscache_map = dict()
        self._blocksindex_map = dict()

    def _inode_to_path(self, inode):
        try:
            val = self._inode_path_map[inode]
        except KeyError:
            raise FUSEError(errno.ENOENT)

        if isinstance(val, set):
            # In case of hardlinks, pick any path
            val = next(iter(val))
        return val

    def _add_path(self, inode, path):
        log.debug('_add_path for %d, %s', inode, path)
        self._lookup_cnt[inode] += 1

        # With hardlinks, one inode may map to multiple paths.
        if inode not in self._inode_path_map:
            self._inode_path_map[inode] = path
            return

        val = self._inode_path_map[inode]
        if isinstance(val, set):
            val.add(path)
        elif val != path:
            self._inode_path_map[inode] = {path, val}

    async def forget(self, inode_list):
        for (inode, nlookup) in inode_list:
            if self._lookup_cnt[inode] > nlookup:
                self._lookup_cnt[inode] -= nlookup
                continue
            log.debug('forgetting about inode %d', inode)
            assert inode not in self._inode_fd_map
            del self._lookup_cnt[inode]
            try:
                del self._inode_path_map[inode]
            except KeyError:  # may have been deleted
                pass

    async def lookup(self, inode_p, name, ctx=None):
        name = fsdecode(name)
        log.debug('lookup for %s in %d', name, inode_p)
        path = os.path.join(self._inode_to_path(inode_p), name)
        attr = self._getattr(path=path)
        if name != '.' and name != '..':
            self._add_path(attr.st_ino, path)
        return attr

    async def getattr(self, inode, ctx=None):
        if inode in self._inode_fd_map:
            return self._getattr(fd=self._inode_fd_map[inode])
        else:
            return self._getattr(path=self._inode_to_path(inode))

    def _getattr(self, path=None, fd=None):
        assert fd is None or path is None
        assert not(fd is None and path is None)
        total_size = None
        try:
            if fd is None:
                stat = os.lstat(path)
                t_path = path
            else:
                stat = os.fstat(fd)
                inode = self._fd_inode_map[fd]
                t_path = self._inode_to_path(inode)

            try:
                total_size = FileObject(t_path).header.get_size()
            except Exception as ex:
                log.debug(f"{ex}")
        except OSError as exc:
            raise FUSEError(exc.errno)

        entry = pyfuse3.EntryAttributes()
        for attr in ('st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
                     'st_rdev', 'st_size', 'st_atime_ns', 'st_mtime_ns',
                     'st_ctime_ns'):
            setattr(entry, attr, getattr(stat, attr))

        # Correct file size if is compressed
        if total_size:
            entry.st_size = total_size

        entry.generation = 0
        entry.entry_timeout = 0
        entry.attr_timeout = 0
        entry.st_blksize = 512
        entry.st_blocks = (
            (entry.st_size+entry.st_blksize-1) // entry.st_blksize)

        return entry

    async def readlink(self, inode, ctx):
        path = self._inode_to_path(inode)
        try:
            target = os.readlink(path)
        except OSError as exc:
            raise FUSEError(exc.errno)
        return fsencode(target)

    async def opendir(self, inode, ctx):
        return inode

    async def readdir(self, inode, off, token):
        path = self._inode_to_path(inode)
        log.debug('reading %s', path)
        entries = []
        for name in os.listdir(path):
            if name == '.' or name == '..':
                continue
            attr = self._getattr(path=os.path.join(path, name))
            entries.append((attr.st_ino, name, attr))

        log.debug('read %d entries, starting at %d', len(entries), off)

        # This is not fully posix compatible. If there are hardlinks
        # (two names with the same inode), we don't have a unique
        # offset to start in between them. Note that we cannot simply
        # count entries, because then we would skip over entries
        # (or return them more than once) if the number of directory
        # entries changes between two calls to readdir().
        for (ino, name, attr) in sorted(entries):
            if ino <= off:
                continue
            if not pyfuse3.readdir_reply(
                    token, fsencode(name), attr, ino):
                break
            self._add_path(attr.st_ino, os.path.join(path, name))

    def _forget_path(self, inode, path):
        log.debug('forget %s for %d', path, inode)
        val = self._inode_path_map[inode]
        if isinstance(val, set):
            val.remove(path)
            if len(val) == 1:
                self._inode_path_map[inode] = next(iter(val))
        else:
            del self._inode_path_map[inode]

    async def statfs(self, ctx):
        root = self._inode_path_map[pyfuse3.ROOT_INODE]
        stat_ = pyfuse3.StatvfsData()
        try:
            statfs = os.statvfs(root)
        except OSError as exc:
            raise FUSEError(exc.errno)
        for attr in ('f_bsize', 'f_frsize', 'f_blocks', 'f_bfree', 'f_bavail',
                     'f_files', 'f_ffree', 'f_favail'):
            setattr(stat_, attr, getattr(statfs, attr))
        stat_.f_namemax = statfs.f_namemax - (len(root)+1)
        return stat_

    async def open(self, inode, flags, ctx):
        if inode in self._inode_fd_map:
            fd = self._inode_fd_map[inode]
            self._fd_open_count[fd] += 1
            return pyfuse3.FileInfo(fh=fd)
        assert flags & os.O_CREAT == 0

        file_path = self._inode_to_path(inode)
        try:
            fd = os.open(file_path, flags)
        except OSError as exc:
            raise FUSEError(exc.errno)

        try:
            fobj = FileObject(file_path)
            self._fileobject_map[fd] = fobj
            self._fileobject_path_map[file_path] = fobj

            max_cache = int(2**23 / fobj.header.get_blocksize())
            self._blockscache_map[fd] = deque(
                [], max_cache)  # FIXME: Apropiate size
            self._blocksindex_map[fd] = deque([], max_cache)
        except NotCompressedFile:
            # If file is not compressed, treat it as general case
            pass

        self._inode_fd_map[inode] = fd
        self._fd_inode_map[fd] = inode
        self._fd_open_count[fd] = 1
        return pyfuse3.FileInfo(fh=fd)

    async def read(self, fd, offset, length):
        if fd not in self._fileobject_map:
            # Not compressed files
            os.lseek(fd, offset, os.SEEK_SET)
            log.debug('READ of %s, from %d with %d size', fd, offset, length)
            return os.read(fd, length)

        block_start = math.ceil(
            offset / self._fileobject_map[fd].header.get_blocksize())
        total_blocks = math.ceil(
            length / self._fileobject_map[fd].header.get_blocksize())

        out_data = bytearray()
        blocksize = self._fileobject_map[fd].header.get_blocksize()

        idx_quee = self._blocksindex_map[fd]
        cache_queu = self._blockscache_map[fd]

        for bcount in range(total_blocks):
            b = block_start + bcount
            if b in idx_quee:
                idx_data = idx_quee.index(b)
                data = cache_queu[idx_data]

                ## Do some temporal cache by moving the hit to the top of the queue
                if idx_data != 0:
                    # Move our target to the end
                    idx_quee.rotate(len(idx_quee) - 1 - idx_data)
                    cache_queu.rotate(len(cache_queu) - 1 - idx_data)

                    # Append to first
                    idx_quee.insert(len(idx_quee) - 1 - idx_data, idx_quee.pop())
                    cache_queu.insert(len(cache_queu) - 1 -
                                    idx_data, cache_queu.pop())

                    # Reorder back
                    idx_quee.rotate(-(len(idx_quee) - 1 - idx_data))
                    cache_queu.rotate(-(len(cache_queu) - 1 - idx_data))

            else:
                # Cache hit error. Read from disk
                cache_spacial = 3

                if bcount + cache_spacial >= total_blocks:
                    # Exceeded EOF. Readjust size
                    cache_spacial = total_blocks - bcount
                    assert(cache_spacial != 0)



                data_blocks = self._fileobject_map[fd].read_block(
                    b, file_descriptor=fd, count=cache_spacial)

                for i in reversed(range(cache_spacial)):
                    block = data_blocks[i*blocksize:i*blocksize + blocksize]
                    if i == 0:
                        # What we really asked 
                        data = block
                    idx_quee.appendleft(b + i)
                    cache_queu.appendleft(block)

            if bcount == total_blocks - 1:  # Last element
                last_size = length % self._fileobject_map[fd].header.get_blocksize(
                )
                out_data += data[0:last_size]
            else:
                out_data += data

        return out_data

    async def release(self, fd):
        if self._fd_open_count[fd] > 1:
            self._fd_open_count[fd] -= 1
            return

        del self._fd_open_count[fd]
        inode = self._fd_inode_map[fd]
        del self._inode_fd_map[inode]
        del self._fd_inode_map[fd]

        if fd in self._fileobject_map:
            del self._fileobject_map[fd]
            del self._fileobject_path_map[self._inode_to_path(inode)]
            del self._blockscache_map[fd]
            del self._blocksindex_map[fd]
        try:
            os.close(fd)
        except OSError as exc:
            raise FUSEError(exc.errno)

def init_logging(debug=False):
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(threadName)s: '
                                  '[%(name)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    if debug:
        handler.setLevel(logging.DEBUG)
        root_logger.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)


def mount_fuse(source, mountpoint):
    init_logging(True)
    operations = Operations(str(source))

    log.debug('Mounting...')
    fuse_options = set(pyfuse3.default_options)
    fuse_options.add('fsname=passthroughfs')
    # if options.debug_fuse:
    #     fuse_options.add('debug')
    pyfuse3.init(operations, str(mountpoint), fuse_options)

    try:
        log.debug('Entering main loop..')
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close(unmount=True)
        raise

    log.debug('Unmounting..')
    pyfuse3.close()
