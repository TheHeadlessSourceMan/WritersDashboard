#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
Juggle info about settings
"""
import typing
import os
from paths import URLCompatible, asUrl


class Settings:
    """
    A general-purpose group of settings
    """

    SAVE_FIELDS:typing.List[str]=[
        'workingHoursPerDayPerBook','workingDaysPerWeek','targetWordcount',
        'workingHoursPerDay','simultaneousBooks','projectsDirectory',
        'writingApp']
    FIELD_FORMAT:typing.List[type]=[
        float,float,float,
        float,float,str,str]

    def __init__(self):
        # TODO: the default only works for windows
        self.projectsDirectory=os.environ['USERPROFILE']+os.sep+'Documents'
        self.loadSettings()

    def loadSettings(self,location:URLCompatible='settings.ini')->None:
        """
        TODO: data should be able to live in
        a spreadsheet, google doc, whatever
        """
        self.settings=[]
        for line in asUrl(location).read():
            line=line.split('=',1)
            if len(line)>1:
                k=line[0].strip()
                v=line[1].strip()
                try:
                    idx=self.SAVE_FIELDS.index(k)
                except AttributeError:
                    continue
                v=self.FIELD_FORMAT[idx](v)
                setattr(self,k,v)

    def saveSettings(self,location:URLCompatible='settings.ini')->None:
        """
        TODO: data should be able to live in
        a spreadsheet, google doc, whatever
        """
        f=open(location,'wb')
        for k in Settings.SAVE_FIELDS:
            f.write(k+'='+str(getattr(self,k))+'\n')
        f.flush()
        f.close()


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                kv=[a.strip() for a in arg.split('=',1)]
                if kv[0] in ['-h','--help']:
                    printhelp=True
                else:
                    print('ERR: unknown argument "'+kv[0]+'"')
            else:
                print('ERR: unknown argument "'+arg+'"')
    if printhelp:
        print('Usage:')
        print('  settings.py [options]')
        print('Options:')
        print('   NONE')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
