# coding=utf-8
import os
import time

from requests_toolbelt import MultipartEncoder

from .api import Api


class FileStation(Api):
    cgi_path = 'entry.cgi'

    """Access Synology FileStation information"""
    add = 'real_path,size,owner,time,perm'

    def get_info(self):
        """Provide File Station information"""
        return self.req(self.endpoint('SYNO.FileStation.Info',
                                      cgi = self.cgi_path, method = 'get'))

    def list_share(self, writable_only = False, limit = 25, offset = 0,
                   sort_by = 'name', sort_direction = 'asc', additional = False):
        """List all shared folders"""
        return self.req(self.endpoint(
            'SYNO.FileStation.List',
            cgi = self.cgi_path,
            method = 'list_share',
            version = '2',
            extra = {
                'onlywritable': writable_only,
                'limit': limit,
                'offset': offset,
                'sort_by': sort_by,
                'sort_direction': sort_direction,
                'additional': self.add if additional else ''
            }
        ))

    def list(self, path, limit = 25, offset = 0, sort_by = 'name',
             sort_direction = 'asc', pattern = '', filetype = 'all',
             additional = False):
        """Enumerate files in a given folder"""
        return self.req(self.endpoint(
            'SYNO.FileStation.List',
            cgi = self.cgi_path,
            method = 'list',
            version = '2',
            extra = {
                'folder_path': path,
                'limit': limit,
                'offset': offset,
                'sort_by': sort_by,
                'sort_direction': sort_direction,
                'pattern': pattern,
                'filetype': filetype,
                'additional': self.add if additional else ''
            }
        ))

    def get_file_info(self, path, additional = False):
        """Get information of file(s)"""
        return self.req(self.endpoint(
            'SYNO.FileStation.List',
            cgi = self.cgi_path,
            method = 'getinfo',
            extra = {
                'path': path,
                'additional': self.add if additional else ''
            }
        ))

    def search(self, path, pattern):
        """Search for files/folders"""
        start = self.req(self.endpoint(
            'SYNO.FileStation.Search',
            cgi = self.cgi_path,
            method = 'start',
            extra = {
                'folder_path': path,
                'pattern': pattern
            }
        ))
        if not 'taskid' in start.keys():
            raise NameError('taskid not in response')

        while True:
            time.sleep(0.5)
            file_list = self.req(self.endpoint(
                'SYNO.FileStation.Search',
                cgi = self.cgi_path,
                method = 'list',
                extra = {
                    'taskid': start['taskid'],
                    'limit': -1
                }
            ))
            if file_list['finished']:
                result_list = []
                for item in file_list['files']:
                    result_list.append(item['path'])
                return result_list

    def dir_size(self, path):
        """
        Get the accumulated size of files/folders within folder(s)

        Returns:
            size in octets
        """
        start = self.req(self.endpoint(
            'SYNO.FileStation.DirSize',
            cgi = self.cgi_path,
            method = 'start',
            extra = {'path': path}
        ))
        if not 'taskid' in start.keys():
            raise NameError('taskid not in response')

        while True:
            time.sleep(10)
            status = self.req(self.endpoint(
                'SYNO.FileStation.DirSize',
                cgi = self.cgi_path,
                method = 'status',
                extra = {'taskid': start['taskid']}
            ))
            if status['finished']:
                return int(status['total_size'])

    def md5(self, path):
        """Get MD5 of a file"""
        start = self.req(self.endpoint(
            'SYNO.FileStation.MD5',
            cgi = self.cgi_path,
            method = 'start',
            extra = {'file_path': path}
        ))
        if not 'taskid' in start.keys():
            raise NameError('taskid not in response')

        while True:
            time.sleep(10)
            status = self.req(self.endpoint(
                'SYNO.FileStation.MD5',
                cgi = 'FileStation/file_md5.cgi',
                method = 'status',
                extra = {'taskid': start['taskid']}
            ))
            if status['finished']:
                return status['md5']

    def permission(self, path):
        """Check if user has permission to write to a path"""
        return self.req(self.endpoint(
            'SYNO.FileStation.CheckPermission',
            cgi = self.cgi_path,
            method = 'write',
            extra = {
                'path': path,
                'create_only': 'false'
            }
        ))

    def delete(self, path):
        """
        Delete file(s)/folder(s)

        Using the blocking method for now
        """
        return self.req(self.endpoint(
            'SYNO.FileStation.Delete',
            cgi = self.cgi_path,
            method = 'start',
            version = '2',
            extra = {'path': path}
        ))

    def create(self, path, name, force_parent = True, additional = False):
        """
        Create folders

        Does not support several path/name tuple as the API does
        """
        return self.req(self.endpoint(
            'SYNO.FileStation.CreateFolder',
            cgi = self.cgi_path,
            method = 'create',
            extra = {
                'name': name,
                'folder_path': path,
                'force_parent': force_parent,
                'additional': self.add if additional else ''
            }
        ))

    def rename(self, path, name, additional = False):
        """Rename a file/folder"""
        return self.req(self.endpoint(
            'SYNO.FileStation.Rename',
            cgi = self.cgi_path,
            method = 'rename',
            extra = {
                'name': name,
                'path': path,
                'additional': self.add if additional else ''
            }
        ))

    def extract(self, path, destpath):
        """Get thumbnail of file"""
        return self.req(self.endpoint(
            'SYNO.FileStation.Extract',
            cgi = self.cgi_path,
            method = 'start',
            extra = {
                'file_path': path,
                'dest_folder_path': destpath,
                'keep_dir': 'true',
                'create_subfolder': 'true',
                'overwrite': 'true'
            }
        ))

    def thumb(self, path, size = 'small', rotate = '0'):
        """Get thumbnail of file"""
        return self.req_binary(self.endpoint(
            'SYNO.FileStation.Thumb',
            cgi = self.cgi_path,
            method = 'get',
            extra = {
                'path': path,
                'size': size,
                'rotate': rotate
            }
        ))

    def download(self, path, mode = 'open', **kwargs):
        """Download files/folders"""
        return self.req_binary(self.endpoint(
            'SYNO.FileStation.Download',
            cgi = self.cgi_path,
            method = 'download',
            extra = {
                'path': path,
                'mode': mode
            }
        ), **kwargs)

    def upload(self, remotePath, localPath, overwrite = True):
        """Upload file"""
        dir = os.path.dirname(remotePath)
        file = os.path.basename(remotePath)
        m = MultipartEncoder(
            fields = {'create_parents': 'true',
                      'overwrite': 'true' if overwrite else 'false',
                      'path': dir,
                      'file': (file, open(localPath, 'rb'), 'application/octet-stream')
                      }
        )
        return self.req_formdata(self.endpoint(
            'SYNO.FileStation.Upload',
            cgi = self.cgi_path,
            version = '2',
            method = 'upload'),
            m,
            {'Content-Type': m.content_type}
        )

    def backgroundTask(self):
        """Get background task status"""
        return self.req(self.endpoint(
            'SYNO.FileStation.BackgroundTask',
            cgi = self.cgi_path,
            method = 'list',
            version = '3',
        ))

    def clearBackgroundTask(self, taskid):
        """Clear finished background task"""
        return self.req(self.endpoint(
            'SYNO.FileStation.BackgroundTask',
            cgi = self.cgi_path,
            method = 'clear_finished',
            version = '3',
            extra = {
                'taskid': taskid
            }
        ))

    def waitForTaskFinished(self, taskid, timeout = 30):
        wait = 0
        taskwait = {'taskid': taskid, 'success': False, 'wait': wait}
        while wait <= timeout:
            self.clearBackgroundTask(taskid)
            taskList = self.backgroundTask()
            if taskid in [t['taskid'] for t in taskList['tasks']]:
                wait = wait + 1
                taskwait = {'taskid': taskid, 'success': False, 'wait': wait}
                time.sleep(1)
            else:
                taskwait = {'taskid': taskid, 'success': True, 'wait': wait}
                break
        return taskwait