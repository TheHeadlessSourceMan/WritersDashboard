#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
Juggle info about projects
"""
import typing
import os
import datetime
from paths import URL,URLCompatible
from .uiRepresentation import UIRepresentation
from .settings import Settings
from .stageInfo import StageInfo, StageInfos


def _dateparse(s:str)->datetime.datetime:
    return datetime.datetime.strptime(s,'%m/%d/%y')


class Project(UIRepresentation):
    """
    Represents a single writing project
    """

    SAVE_FIELDS:typing.List[str]=[
        'priority','activeStatus','workingTitle','series',
        'targetWords','currentWords',
        'stage','stagePercent','desiredETA','blockedBy','documentLocation']
    FIELD_FORMAT:typing.List[type]=[
        int,str,str,str,int,int,
        int,float,_dateparse,str,str]

    def __init__(self,settings:Settings,stageInfo:StageInfo):
        UIRepresentation.__init__(self) # TODO: add my template
        self.settings:Settings=settings
        self.stageInfo:StageInfo=stageInfo
        self.priority:int=99
        self.activeStatus:str='planned'
        self.workingTitle:str=None
        self.series:str=None
        self.targetWords:int=60000
        self.currentWords:int=0
        self.stage:int=0
        self.stagePercent:float=0
        self.desiredETA:datetime.datetime=None
        self.blockedBy:typing.List[str]=None
        self.documentLocation:URL=None

    @property
    def title(self)->str:
        """ same as workingTitle """
        return self.workingTitle
    @title.setter
    def title(self,title:str):
        self.workingTitle=title

    @property
    def currentStageInfo(self)->StageInfo:
        """
        information about the current stage we are on
        """
        return self.stageInfo[self.stage]

    @property
    def totalPercent(self)->float:
        """
        percent of the total project that is currently complete
        """
        return 1-self.totalHoursRemaining/self.stageInfo.totalHours

    @property
    def hoursRemainingInStage(self)->int:
        """
        how many hours remain in the current stage we are on
        """
        return self.currentStageInfo.totalHours*(1-self.stagePercent)

    @property
    def totalHoursRemaining(self)->int:
        """
        how many hours remain
        """
        hours=self.hoursRemainingInStage
        for stageNum in range(int(self.stage)-1):
            hours+=self.stageInfo[stageNum].totalHours
        return hours

    @property
    def ETA(self)->datetime.datetime:
        """
        the current estimate for when this will be completed
        """
        if isinstance(self.settings.workingHoursPerDayPerBook,str):
            self.settings.workingHoursPerDayPerBook=\
                self.settings.workingHoursPerDayPerBook
        hours=self.totalHoursRemaining/self.settings.workingHoursPerDayPerBook
        return datetime.datetime.now()+datetime.timedelta(hours=hours)

    @property
    def stageGoal(self)->str:
        """
        the goal for the current stage
        """
        return self.currentStageInfo.goal

    @property
    def daysAhead(self)->int:
        """
        Returns positive number of days ahead of schedule you are.

        If you are behind (not that that would ever happen) then
        the value is negative.
        """
        if self.desiredETA is None or self.ETA is None:
            return 0
        return (self.desiredETA-self.ETA).days

    def open(self)->None:
        """
        open the main project file using the associated os program

        will do nothing if there is no associated documentLocation
        """
        import subprocess
        if self.documentLocation is None:
            print('No file associated with',self.title)
            return
        # TODO: this is a windows thing.  For linux, use xdg-open
        cmd='start "" "'+self.documentLocation+'"'
        print('>>',cmd)
        po=subprocess.Popen(cmd,shell=True,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out,err=po.communicate()
        err=err.strip()
        if err:
            print(err)
        print(out)

    def __repr__(self)->str:
        ret=[]
        for k in self.SAVE_FIELDS:
            if hasattr(self,k):
                ret.append(k+'='+str(getattr(self,k)))
        for k in ('totalPercent','hoursRemainingInStage',
            'totalHoursRemaining','ETA','stageGoal'):
            #
            ret.append(k+'='+str(getattr(self,k)))
        return '\n'.join(ret)


class Projects:
    """
    A set of projects
    """

    def __init__(self,settings:Settings,stageInfo:StageInfos):
        self.settings:Settings=settings
        self.stageInfo:StageInfos=stageInfo
        self.loadProjects()

    def _unCamel(self,title:str)->str:
        """
        undo potential camel case in a title
        """
        title=title.strip()
        if title.find(' ')>0: # assume that they knew how to use a spacebar
            return title
        t2=[]
        lastLower=False
        title=title[0].upper()+title[1:]
        for letter in title:
            if lastLower!=letter.isupper():
                t2.append(' ')
            t2.append(letter)
        return ''.join(t2)

    def _makeComparable(self,s:str)->str:
        """
        make a string more permissively comparable
        """
        return s.split('-',1)[0].split('(',1)[0].replace(' ','').\
            replace('_','').replace(':','').replace(';','').lower()

    def _titlecompare(self,title1:str,title2:str)->bool:
        """
        generously compare titles, being insensitive to
        case, space, or punctuation
        """
        if title1==title2:
            return True
        return self._makeComparable(title1)==self._makeComparable(title2)

    def _projectFromFile(self,path:URLCompatible,seriesHint:str=None)->Project:
        """
        create a project object based on an editor file

        :param seriesHint: if we can't get the series name any other way
            use this as the name

        TODO: with the help of bookMaker we can get word counts
            and everything else!
        """
        project=Project(self.settings,self.stageInfo)
        title=path\
            .rsplit(os.sep,1)[-1]\
            .rsplit('.',1)[0]\
            .rsplit('-',1)[0]\
            .strip()
        title=self._unCamel(title)
        project.workingTitle=title
        project.series=seriesHint
        project.documentLocation=path
        return project

    def _directoryLooksLikeProject(self,
        directory:URLCompatible,
        seriesHint:str=None
        )->bool:
        """
        Determines if the directory looks like a project.

        If so, returns a filled out project object.  If not, returns None.
        """
        foundFile=None
        foundPriority=1000
        writingFileExtensions=(
            'msk','celtx','odt','doc','docx') # in priority order!
        for filename in os.listdir(directory):
            fullPath=directory+os.sep+filename # make it into a full path
            if not os.path.isfile(fullPath):
                continue
            ext=filename.rsplit('.',1)
            if len(ext)<2:
                continue
            try:
                idx=writingFileExtensions.index(ext[1])
            except ValueError:
                continue
            if idx<foundPriority:
                foundFile=fullPath
                foundPriority=idx
            elif idx==foundPriority: # if they are the same extension, go with the newest # noqa: E501 # pylint: disable=line-too-long
                if os.path.getmtime(foundFile)<os.path.getmtime(fullPath):
                    foundFile=fullPath
        if foundFile is not None:
            foundFile=self._projectFromFile(foundFile,seriesHint)
        return foundFile

    def _directoryLooksLikeSeries(self,directory:URLCompatible)->bool:
        """
        Determines if the directory looks like a series.

        That is, a directory containing subdirectories that look like projects.

        returns an array of filled out project objects.
            It is empty if it isn't a series.
        """
        foundProjects=[]
        seriesHint=self._unCamel(
            directory\
            .rsplit(os.sep,1)[-1]\
            .rsplit('.',1)[0]\
            .strip())
        for d in os.listdir(directory):
            d=directory+os.sep+d # make it into a full path
            if not os.path.isdir(d):
                continue
            project=self._directoryLooksLikeProject(d,seriesHint)
            if project is not None:
                foundProjects.append(project)
        return foundProjects

    def _findProjects(self)->typing.Generator[Project,None,None]:
        """
        scan the projects directory specified in the settings.ini
            projectsDirectory=value
            (if not set, this defaults to the "my documents" schtick)

        returns [Project] that can be matched by name
            with existing Project objects
        """
        for d in os.listdir(self.settings.projectsDirectory):
            d=self.settings.projectsDirectory+os.sep+d # make it into a full path # noqa: E501 # pylint: disable=line-too-long
            if not os.path.isdir(d):
                continue
            project=self._directoryLooksLikeProject(d,None)
            if project is not None:
                yield project
            else:
                pass #foundProjects.extend(self._directoryLooksLikeSeries(d))

    def scanProjects(self
        )->typing.Tuple[
            typing.List[Project],
            typing.List[Project],
            typing.List[typing.Tuple[Project,URL]]
        ]:
        """
        scan the projects directory specified in the settings.ini
            projectsDirectory=value
            (if not set, this defaults to the "my documents" schtick)

        the goal is to find:
            * projects that have gone missing
            * new projects that can be added
            * projects that can be linked to those already in the database

        returns ([missingProjects],[newProjects],[(project,suggestedFile)])
        """
        foundProjects:typing.List[Project]=list(self._findProjects())
        missingProjects:typing.List[Project]=[]
        newProjects:typing.List[Project]=[]
        suggestedLinks:typing.List[typing.Tuple[Project,URL]]=[]
        for p in self.projects:
            if p.documentLocation is None \
                or not os.path.exists(p.documentLocation): # noqa: E129
                # try to find a project that matches
                found=False
                for p2 in foundProjects:
                    if self._titlecompare(p.title,p2.title):
                        suggestedLinks.append((p,p2.documentLocation))
                        found=True
                        break
                if not found and p.documentLocation is not None: # missing!
                    missingProjects.append(p)
        # now we have to search the other way to see what's new
        for p in foundProjects:
            matched=False
            for p2 in self.projects:
                if p.documentLocation is not None \
                    and p.documentLocation==p2.documentLocation: # noqa: E129
                    #
                    matched=True
                    break
                if self._titlecompare(p.title,p2.title):
                    matched=True
                    break
            if not matched:
                newProjects.append(p)
        return missingProjects,newProjects,suggestedLinks

    def loadProjects(self,
        location:URLCompatible='projects.csv',
        split_char:str=','
        )->None:
        """
        TODO: data should be able to live in
        a spreadsheet, google doc, whatever
        """
        self.projects=[]
        header=None
        f=open(location,'rb')
        lineNo=1
        for line in f:
            line=line.strip()
            if line:
                line=line.split(split_char)
                if header is None:
                    header=[]
                    fmts=[]
                    for h in line:
                        h=h.strip().replace(' ','').replace(r'%','Percent')
                        try:
                            idx=Project.SAVE_FIELDS.index(h)
                        except AttributeError:
                            print(f'Skipping column "{h}"')
                            header.append(None)
                            fmts.append(None)
                            continue
                        header.append(h)
                        fmts.append(Project.FIELD_FORMAT[idx])
                else:
                    proj=Project(self.settings,self.stageInfo)
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
                    self.projects.append(proj)
            lineNo+=1

    def saveProjects(self,
        location:URLCompatible='projects.csv',
        split_char:str=','
        )->None:
        """
        TODO: data should be able to live in
            a spreadsheet, google doc, whatever
        """
        f=open(location,'wb')
        f.write(split_char.join(Project.SAVE_FIELDS))
        f.write('\n')
        for p in self.projects:
            line=[]
            for k in Project.SAVE_FIELDS:
                line.append(str(getattr(p,k)))
            f.write(split_char.join(line))
            f.write('\n')
        f.flush()
        f.close()

    def getByName(self,name:str)->Project:
        """
        If this doesn't match exactly one project, raises an exception
        """
        found=None
        for p in self.projects:
            if p.title==name:
                if found is not None:
                    raise Exception('Project name ambiguious.')
                found=p
        if found:
            return found
        # no?  try a caseless comparison
        for p in self.projects:
            if self._titlecompare(p.title,name):
                if found is not None:
                    raise Exception(
                        'Project name ambiguious - '+\
                        p.title+\
                        ' <-> '+\
                        found.title)
                found=p
        if found:
            return found
        raise Exception('Unable to find matching project.')

    def top(self,n:int=1)->typing.List[Project]:
        """
        Get the top priority project(s) in terms of priority*10+daysAhead

        Always returns list
        """
        n=min(n,len(self.projects))
        s=sorted(self.projects,key=lambda element: \
            element.priority*10+element.daysAhead)
        for a in s:
            if a.activeStatus!='active':
                s.remove(a)
        return s[0:n]

    def __len__(self)->int:
        return len(self.projects)
    def __getitem__(self,idx):
        return self.projects[idx]
    def __iter__(self)->typing.Iterator[Project]:
        return iter(self.projects)

    def __repr__(self)->str:
        return '\n================\n'.join([str(p) for p in self.projects])


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
        print('  projects.py [options]')
        print('Options:')
        print('   NONE')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
