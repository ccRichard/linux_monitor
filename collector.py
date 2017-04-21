#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Date       : 2016-11-28 17:25:25
# Author     : cc
# Description:

from __future__ import generators
import os
import time
import subprocess
import requests


# 配置说明：
# 'cmds'：待收集的进程cmd，根据其获取pid，验证方式：ps -C cmd
# 'dstat_path'：dstat工具所在的目录
# 'sys_output'：记录系统数据的csv文件名，False表示不打印不记录，''表示只打印不记录
# 'process_output'：记录进程数据的csv文件名，False表示不打印不记录，''表示只打印不记录
test_config = {
    'cmds':'java,beam.smp,top,memcached',
    'dstat_path':'/home/x9/ccc/dstat-master',
    'sys_output':'sys_stat.csv',
    'process_output':'process_stat.csv'
}


# 生成给dstat读取配置的dt_temp.conf文件
def creat_temp():
    filename = test_config['dstat_path'].rstrip('/') + '/dt_temp.conf'
    f = open(filename, 'w')
    f.write('cmds:%s' % test_config['cmds'])
    f.close()

    csvfiles = [test_config['sys_output'], test_config['process_output']]
    for csv in csvfiles:
        if csv == '':
            continue
        elif csv == False:
            continue
        if os.path.exists(csv):
            if not csv_bak(csv):
                print('%s file can not be rename!' % csv)
                return False
        
    return True


# 启动性能收集工具进程
def stat_start(cfg = test_config):
    processes = list()
    dstat_cmd = '%s/dstat' % cfg['dstat_path'].rstrip('/')
    sys_csv = cfg['sys_output']
    process_csv = cfg['process_output']

    # 采集linux系统性能数据
    if sys_csv == '':
        sys_stat = subprocess.Popen([dstat_cmd, '-tcmdn'])
    elif sys_csv == False:
        sys_stat = False
    else:
        sys_stat = subprocess.Popen([dstat_cmd, '-tcmdn', '--output', sys_csv])

    # 采集进程性能数据
    if process_csv == '':
        process_stat = subprocess.Popen([dstat_cmd, '--process'])
    elif process_csv == False:
        process_stat = False
    else:
        process_stat = subprocess.Popen([dstat_cmd, '--process', '--output', process_csv])

    if sys_stat:
        processes.append(sys_stat)
    if process_stat:
        processes.append(process_stat)

    return processes


# ctrl+c中止采集
def stat_stop(processes):
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for process in processes:
            print(process.pid)
            process.kill()
            return True


# 检查是否有已存在的日志文件，如果有将其重命名
def csv_bak(file, rname=False):
    if os.path.exists(file):
        m_time = os.stat(file).st_mtime
        str_time = time.strftime("%Y%m%d%H%M%S", time.localtime(m_time))
        old_name = os.path.splitext(file)
        new_name = '%s_%s%s' % (old_name[0], str_time, old_name[1])
        os.rename(file, new_name)
        if rname:
            return new_name
        else:
            return True


# 发送文件到数据平台
def send_reports(filelist, ip='127.0.0.1', port='5000'):
    for file in filelist:
        filename = file
        if file == test_config['sys_output'] or test_config['process_output']:
            filename = csv_bak(file, True)
        f = {'file': open(filename, 'rb')}
        r_address = 'http://%s:%s' % (ip, port)
        try:
            r = requests.post(r_address, files=f, timeout=10)
            print('send %s success!' % filename)
        except Exception as ex:
            print('send %s failed, please upload manually.' % filename)


# main主逻辑：创建给dstat-process读取的temp文件，启动进程，监控ctrl+c输入然后中止进程
def main():
    if creat_temp():
        processes = stat_start()
        if stat_stop(processes):
            print(os.getpid())
            print('system and process stats have be collected completely!')
            send_reports([test_config['sys_output'], test_config['process_output']],
                         '100.84.47.220', '5000')
    else:
        print('can not create temp config file!')


if __name__ == '__main__':
    main()




