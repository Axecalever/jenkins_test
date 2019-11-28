#!/usr/bin/env python
import os
import shutil
import time
import sys
import json
import traceback
import logging
import commands

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s : %(message)s', '%Y-%m-%d %H:%M:%S')
fileHandler = logging.FileHandler('log.txt')
streamHandler = logging.StreamHandler()
fileHandler.setFormatter(formatter)
streamHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
logger.setLevel(logging.INFO)


def create_folder(newpath):
    """ Creates the <newpath> if does not exist"""
    
    try:
        if not os.path.exists(newpath):
            logger.info('Creating path %s' % (newpath))
            os.makedirs(newpath)
    except:
        logger.exception('Exception:')
        
def copy_files(srcdir, dest, filetype):
    """ Copy all files of type <filetype>, from directory <srcdir> located in abspath(__file__), to <dest> path """
    
    try:
        logger.info('Copying all %s files from %s to %s'  % (filetype, srcdir, dest))
        create_folder(dest)
        #srcdirpath = str(os.path.dirname(os.path.abspath(__file__))) + srcdir
        srcdirpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), srcdir)
        for file in os.listdir(srcdirpath):
            if file.endswith(filetype):
                #src = srcdirpath + "/" + os.path.basename(file)
                src = os.path.join(srcdirpath, os.path.basename(file))
                x = 'y'
                #if os.path.exists(dest + os.path.basename(file)) and filetype == '.conf':
                if os.path.exists(os.path.join(dest, os.path.basename(file))) and filetype == '.conf':
                    x = raw_input('File %s already exists, overwrite? [y/N]' % (os.path.basename(file))).lower()
                if x in ['y', 'yes', 'Y', 'Yes', 'YES']:
                    logger.info('Copying %s' % os.path.basename(file))
                    shutil.copy(src, dest)
                else:
                    logger.info('Skipping file %s' % os.path.basename(file))
    except:
        logger.exception('Exception:')
    
    
def make_executables():
    """ Makes the files in /hannext and /etc/init.d executable """
    
    try:
        logger.info('Making executables')
        os.system("chmod +x /hannext/*")
        os.system("chmod +x /etc/init.d/snc*")
    except:
        logger.exception('Exception:')
    
def download_conf_files():
    """ Downloads the configuration files from the cloud for the collectorid specified in snc.conf"""
    
    try:
        logger.info('Downloading configuration files')
        filePath = '/home/hannext/conf/snc.conf'
        if os.path.exists(filePath):
            try:
                filee = open(filePath)
                snc_cfg = json.load(filee)
                filee.close()
                os.system('python /hannext/sncconfig.py %s' %(snc_cfg['collectorid']))
            except:
                logger.exception('Exception while downloading the configuration files from cloud')
                sys.exit('Please verify that the information in daps.conf and snc.conf is correct then try again')
        else:
            sys.exit('snc.conf not found, please check the configuration files then try again')
    except:
        logger.exception('Exception:')
        
def insert_in_lines(line, lines, insert_index):
    if line not in lines:
        logger.info('Inserting in rc.local %s' % line)
        lines.insert(insert_index, line)
    else:
        logger.info('Already present in rc.local: %s' % line)

def remove_from_lines(line, lines):
    if line in lines:
        logger.info('Removing from rc.local %s' % line)
        lines.remove(line)
    #else:
    #    logger.info('Line not present in rc.local: %s' % line)
    
def update_rclocal():
    try:
        logger.info('Updating /etc/rc.local file')
        filee = open('/etc/rc.local' , 'r')
        lines = filee.readlines()
        filee.close()
        
        line = 'service system-monitor start\n'
        remove_from_lines(line, lines)
        
        line = 'service wan_watchdog_tmr start\n'
        remove_from_lines(line, lines)
        
        try:
            insert_index = lines.index('exit 0\n')
        except:
            try:
                insert_index = lines.index('exit 0')
            except:
                insert_index = len(lines)
        
        line = 'service snc-sysmon start\n'
        insert_in_lines(line, lines, insert_index)
        
        line = 'service snc-watchdog start\n'
        insert_in_lines(line, lines, insert_index)
        
        line = 'echo "Sytem restarted at: $(date)" >> /home/hannext/sysStat.txt\n'
        insert_in_lines(line, lines, insert_index)
        
        line = 'echo "$(date) __________SYSTEM_BOOTED__________" >> /var/log/snc/snc-batmon.log\n'
        insert_in_lines(line, lines, insert_index)

        line = 'chmod +s /ts/sbin/tshwctl\n'
        insert_in_lines(line, lines, insert_index)

        filee = open('/etc/rc.local', 'w')
        filee.write(''.join(lines))
        filee.close()
    except:
        logger.exception('Exception:')

# Install Libraries
# ----------------------------------------------------------------------------------------------------
def install_zmq():
    """ Installs the ZeroMQ library for python """
    
    cwd = str(os.path.dirname(os.path.abspath(__file__)))
    os.chdir('lib/zmq/')
    os.system('./autogen.sh')
    os.system('./configure')
    os.system('make')
    os.system('make check')
    os.system('make install')
    os.chdir(cwd)

def apt_install_online(pkg):
    try:
        logger.info('Installing %s' % pkg)
        os.system('apt-get -y install ' + str(pkg))
    except:
        logger.exception('Cannot install %s' % str(pkg))

    
def pip_install_online(libname):
    logger.info('Installing %s' % libname)
    os.system('pip install ' + str(libname))
    
    
def install_libraries_online():
    """ Installs the required libraries """
    
    try:
        logger.info('Installing libraries')
        os.system('apt-get -y update')
        apt_install_online('python-dev')
        apt_install_online('python-pip')
        apt_install_online('libtool')
        apt_install_online('autoconf')
        apt_install_online('python-paramiko')
	apt_install_online('uuid-dev')
        apt_install_online('libffi-dev')
        pip_install_online('pyserial')
        pip_install_online('requests')
        pip_install_online('pysftp')
        #install_zmq()
        #pip_install_online('pyzmq')
    except:
        logger.exception('Exception:')

def install_libraries_offline():
    # Installing python packages via pip
    # pip download paramiko
    logger.info('Installing library paramiko')
    status, output = commands.getstatusoutput('pip install --use-wheel --no-index --find-links=./libs/paramiko ./libs/paramiko/paramiko-2.1.1-py2.py3-none-any.whl')
    logger.info(output)
    if status != 0:
        sys.exit('Cannot install the paramiko library')
    
    
    
# Backup Old Software
# ----------------------------------------------------------------------------------------------------
def backup_old_soft():
    """ Creates a backup of old snc software installed before installing a new software """
    
    try:
        logger.info('Backing up old software in ./backup')
        create_folder('backup')
        create_folder('backup/pymods')
        create_folder('backup/daemons')
        create_folder('backup/confs')
        
        # Backing up python modules
        if os.path.exists('/hannext'):
            if os.listdir('/hannext/'):
                logger.info('Backing up /hannext...')
                os.system('mv /hannext/*.py backup/pymods')
            else:
                logger.info('No modules found in /hannext to backup')
        else:
            create_folder('/hannext')
            logger.info('/hannext does not exists, creating /hannext')
                
        # Backing up daemons
        if os.path.exists('/etc/init.d'):
            if os.listdir('/etc/init.d'):
                logger.info('Backing up daemons...')
                os.system('mv /etc/init.d/snc* backup/daemons')
                #os.system('mv /etc/init.d/system-monitor backup/daemons')
                #os.system('mv /etc/init.d/wan_watchdog_tmr backup/daemons')
            else:
                logger.info('No daemons found in /etc/init.d to backup')
        else:
            create_folder('/etc/init.d')
            logger.info('/etc/init.d does not exists, creating /etc/init.d')
            
        # Backing up confs
        if os.path.exists('/home/hannext/conf'):
            if os.listdir('/home/hannext/conf/'):
                logger.info('Backing up confs...')
                os.system('cp /home/hannext/conf/* backup/confs')
            else:
                logger.info('No configuration files found in /home/hannext/conf to backup')
        else:
            create_folder('/home/hannext/conf')
            logger.info('/home/hannext/conf does not exists, creating /home/hannext/conf')
    except:
        logger.exception('Exception:')

def update_runlevel():
    try:
        os.system("update-rc.d snc-server defaults")
        os.system("update-rc.d snc-relay defaults")
        os.system("update-rc.d snc-mdtransfer defaults")
        os.system("update-rc.d snc-mdfilecleanup defaults")
        os.system("update-rc.d snc-mdc defaults")
        os.system("update-rc.d snc-configmanager defaults")
        os.system("update-rc.d snc-commandprocessor defaults")
        os.system("update-rc.d snc-server defaults")
        os.system("update-rc.d snc-batmon defaults")
        os.system("update-rc.d snc-alarm defaults")
        os.system("update-rc.d snc-streetlight defaults")
        os.system("update-rc.d snc-sysmon defaults")
        os.system("update-rc.d snc-watchdog defaults")
    except:
        logger.exception('Exception while updating services runlevel:')
            
        
def start():
    logger.info('Starting System Monitor...')
    os.system('service snc-sysmon start')
        
def install():
    
    # Back up old software if it exists
    backup_old_soft()
    
    # Install libraries
    if install_libraries_flag:
        install_libraries_online()
        #apt_install_online('python-paramiko')


    # Copying files
    copy_files("pymods", "/hannext/", ".py")
    copy_files("daemons", "/etc/init.d/", "")
    copy_files("confs", "/home/hannext/conf/", ".conf")

    create_folder('/var/log/snc/')
    
    # Making executables
    make_executables()

    # Downloading configuration files
    download_conf_files()
    
    # Update rc.local file
    update_rclocal()

if __name__== "__main__":
    try:
        if len(sys.argv) < 2:
            sys.exit('Usage: python %s {install|update}' % (sys.argv[0]))

        if sys.argv[1] == 'install':
            install_libraries_flag = 1
        elif sys.argv[1] == 'update':
            install_libraries_flag = 0
        else:
            sys.exit('Usage: python %s {install|update}' % (sys.argv[0]))
        
        install()
        
        if sys.argv[1] == 'install':
            #Updating Runlevel for Services
            update_runlevel()
        
       # start()    
                
    except:
        logger.exception('Exception:')
    else:
        logger.info('Installation Finished')
