#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
Juggle info about stage info
"""
import typing
from paths import URLCompatible, asURL
from .settings import Settings


class StageInfo:
    """
    Information about a particular stage in a writing project
    """

    SAVE_FIELDS:typing.List[str]=[
        'stageNum','name','estimateWorkingDays','estimateWorkingHours','goal']
    FIELD_FORMAT:typing.List[type]=[
        int,str,float,float,str]

    def __init__(self,settings:Settings):
        self.settings:Settings=settings
        self.estimateWorkingHours:int=0
        self.estimateWorkingDays:int=0
        self.goal:str=''

    @property
    def totalHours(self)->int:
        """
        How many total hours is this stage
        """
        return self.estimateWorkingHours+\
            self.estimateWorkingDays*self.settings.workingHoursPerDay


class StageInfos:
    """
    A collection of StageInfo items
    """

    def __init__(self,settings:Settings):
        self.settings:Settings=settings
        self.loadStageInfos()

    def loadStageInfos(self,
        location:URLCompatible='stageInfo.csv',
        split_char:str=','
        )->None:
        """
        TODO: data should be able to live in
        a spreadsheet, google doc, whatever
        """
        self.stageInfos=[]
        header:str=None
        data=asURL(location).read().split('\n')
        lineNo=1
        for line in data:
            line=line.strip()
            if line:
                line=line.split(split_char)
                if header is None:
                    header=[]
                    fmts=[]
                    for h in line:
                        h=h.strip().replace(' ','').replace(r'%','Percent')
                        try:
                            idx=StageInfo.SAVE_FIELDS.index(h)
                        except AttributeError:
                            print('Skipping column "'+h+'"')
                            header.append(None)
                            fmts.append(None)
                            continue
                        header.append(h)
                        fmts.append(StageInfo.FIELD_FORMAT[idx])
                else:
                    proj=StageInfo(self.settings)
                    for i in range(min(len(line),len(header))):
                        k=header[i]
                        if k is not None:
                            try:
                                v=fmts[i](line[i].strip())
                                setattr(proj,k,v)
                            except ValueError:
                                pass
                                # print('ERR: Line',lineNo,' - \
                                #   expected',fmts[i].__class__,
                                #   'for column',header[i],
                                #   'but got "'+line[i]+'" instead.')
                    self.stageInfos.append(proj)
            lineNo+=1

    def saveStageInfos(self,
        location:URLCompatible='stageInfo.csv',
        split_char:str=','
        )->None:
        """
        Save the stage infos to file.

        TODO: data should be able to live in
        a spreadsheet, google doc, whatever
        """
        f=open(location,'wb')
        f.write(split_char.join(StageInfo.SAVE_FIELDS))
        f.write('\n')
        for p in self.stageInfos:
            line=[]
            for k in StageInfo.SAVE_FIELDS:
                line.append(str(getattr(p,k)))
            f.write(split_char.join(line))
            f.write('\n')
        f.flush()
        f.close()

    @property
    def totalHours(self)->int:
        """
        how many total hours are in this stage
        """
        th=0
        for si in self.stageInfos:
            th+=si.totalHours
        return th

    def __len__(self)->int:
        return len(self.stageInfos)

    def __getitem__(self,idx:typing.Union[int,slice])->StageInfo:
        return self.stageInfos[idx]


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
        print('  stageInfos.py [options]')
        print('Options:')
        print('   NONE')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
