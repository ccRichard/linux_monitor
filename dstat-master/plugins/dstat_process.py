#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date       : 2016-11-29 14:22:54
# Author     : cc
# Description:


class dstat_plugin(dstat):
    def __init__(self):
        self.name = 'cc test'
        self.nick = ('time','pid', 'name', 'cpu', 'mem','io_read', 'io_write',)
        self.vars = ('time','pid', 'name', 'cpu', 'mem','io_read', 'io_write',)
        self.type = 's'
        self.width = 16
        self.scale = 0
        self.pidset1 = {}
        self.pidset3 = {}
        # 要监控的进程cmd
        self.pidcmds = self.get_config()
        # self.pidcmds = ['java', 'beam.smp', 'top', 'memcached']
        self.pids = self.get_pid_bycmd()
        self.pidsets = {}


    # 读取配置，获取pidcmds
    def get_config(self):
        pidcmds = []
        path = os.getcwd()
        cfg = path + '/dt_temp.conf'
        if os.path.exists(cfg):
            f = open(cfg, 'r')
            for line in f.readlines():
                if line.find('cmds:') != -1:
                    pidcmds = line.split(':')[-1].split(',')
                    break
            f.close()
            if pidcmds:
                return pidcmds
            else:
                print('cmds can not be found in %s.' % cfg)
        else:
            print('%s can not be found!' % cfg)


    # 通过cmd获取pid
    def get_pid_bycmd(self):
        pids = list()
        for p_cmd in self.pidcmds:
            back_info = os.popen('ps -C %s' % p_cmd).read()
            p_list = back_info.split('\n')[1:]
            for p in p_list:
                if p > '':
                    p = p.lstrip()
                    pids.append(p.split(' ')[0])
        return pids


    def extract(self):
        self.output = ''
        self.pidset2 = {}
        self.pidset4 = {}
        self.val['cpu'] = 0.0
        self.val['mem'] = 0.0
        self.outputs = []

        for pid in proc_pidlist():
            try:
                if pid not in self.pids:
                    continue
                l = proc_splitline('/proc/%s/stat' % pid)
            except IOError:
                continue

            # 获取cpu数据
            if len(l) < 15: continue
            if not self.pidset1.has_key(pid):
                self.pidset1[pid] = 0
            self.pidset2[pid] = long(l[13]) + long(l[14])
            ucpu = (self.pidset2[pid] - self.pidset1[pid]) * 1.0 / elapsed
            name = l[1][1:-1]
            self.val['cpu'] = ucpu
            self.val['pid'] = pid
            self.val['name'] = getnamebypid(pid, name)

            # 获取mem数据
            if len(l) < 23: continue
            umem = int(l[23]) * pagesize
            self.val['mem'] = umem

            # 获取io数据
            try:
                if not self.pidset4.has_key(pid):
                    self.pidset4[pid] = {'rchar:': 0, 'wchar:': 0}
                if not self.pidset3.has_key(pid):
                    self.pidset3[pid] = {'rchar:': 0, 'wchar:': 0}
                for rw in proc_splitlines('/proc/%s/io' % pid):
                    if len(rw) != 2: continue
                    self.pidset4[pid][rw[0]] = int(rw[1])
            except IOError:
                continue
            except IndexError:
                continue

            read_usage = (self.pidset4[pid]['rchar:'] - self.pidset3[pid]['rchar:']) *\
                          1.0 / elapsed
            write_usage = (self.pidset4[pid]['wchar:'] - self.pidset3[pid]['wchar:']) *\
                           1.0 / elapsed

            self.val['io_read'] = read_usage
            self.val['io_write'] = write_usage
            self.val['time'] = time.strftime('%H:%M:%S', time.localtime())

            # 输出内容：时间、pid、进程名、cpu、mem、io_read、io_write
            output = '%-*s %s %s %s %s %s %s' % (self.width-3, self.val['time'],\
                self.val['pid'],  self.val['name'][0:self.width-3],\
                cprint(self.val['cpu'], 'f', 3, 34), cprint(self.val['mem'], 'f', 5, 1024),\
                cprint(self.val['io_read'], 'd', 5, 1024), cprint(self.val['io_write'], 'd', 5, 1024))

            # 多个进程的数据
            self.outputs.append(output)
            # 为输出到csv进行存储
            self.pidsets[pid] = {'time':self.val['time'], 'name':self.val['name'],\
                                 'cpu':self.val['cpu'], 'mem':self.val['mem'],\
                                 'io_read':self.val['io_read'], 'io_write':self.val['io_write']}

        if step == op.delay:
            self.pidset1 = self.pidset2
            self.pidset3 = self.pidset4

        # 输出到屏幕上的内容
        self.output = '\n'.join(self.outputs)


    # 输出到csv文件里的内容：时间、pid、进程名、cpu、mem、io_read、io_write
    def showcsv(self):
        values = []
        for pid in self.pidsets:
            value = '%s,%s,%s,%.2f,%d,%.2f,%.2f' % (self.pidsets[pid]['time'], pid, self.pidsets[pid]['name'],
                self.pidsets[pid]['cpu'], self.pidsets[pid]['mem'],
                self.pidsets[pid]['io_read'], self.pidsets[pid]['io_write'])
            values.append(value)

        return '\n'.join(values)