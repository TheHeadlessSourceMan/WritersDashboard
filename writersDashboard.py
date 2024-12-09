#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This program allows you to monitor several writing projects all at once.
"""
import typing
import os
import htmlui
from WritersDashboard.settings import Settings
from WritersDashboard.stageInfo import StageInfos
from WritersDashboard.projects import Projects


class Dashboard:
    """
    This program allows you to monitor several writing projects all at once.
    """

    def __init__(self):
        self.settings:Settings=Settings()
        self.stageInfo:StageInfos=StageInfos(self.settings)
        self.projects:Projects=Projects(self.settings,self.stageInfo)

    def __repr__(self)->str:
        return str(self.projects)

    def getHtmlControl(self)->htmlui.Javascript:
        """
        get an html control for the dashboard
        """
        code=[]
        # add projects
        for project in self.projects:
            code.append(project.getHtmlControl())
        code='\n'.join(code)
        code=htmlui.setElementContents('app',code)
        return htmlui.Javascript(code)

    def setClassValue(self,guid:str,k:str,v:typing.Any)->htmlui.Javascript:
        """
        Set a value on the class pointed to by guid
        """
        import uiRepresentation
        print(guid,k,v)
        obj=uiRepresentation.UIRepresentation.EVERYTHING[guid]
        setattr(obj,k,v)
        print(guid,k,v)
        return htmlui.Javascript()

    def launchUI(self)->None:
        """
        Launches the UI
        blocks forever
        shuts down program when done
        """
        ui=htmlui.HtmlUI()
        ui.publish(self.getHtmlControl)
        ui.publish(self.setClassValue)
        required=['webkit']
        exitCode=ui.run('WritersDashboard.html',required=required)
        # os._exit() is used to take down all threads
        # (normal exit() would block forever!)
        os._exit(exitCode) # pylint: disable=protected-access


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    d=Dashboard()
    printhelp=False
    if not args:
        printhelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                kv=[a.strip() for a in arg.split('=',1)]
                if kv[0] in ['-h','--help']:
                    printhelp=True
                elif kv[0]=='--ui':
                    d.launchUI()
                elif kv[0]=='--dump':
                    print(d)
                elif kv[0]=='--top':
                    n=4
                    if len(kv)>1:
                        n=int(kv[1])
                    projs=d.projects.top(n)
                    for p in projs:
                        print(p.title,
                            str(p.currentWords)+'/'+str(p.targetWords),
                            p.blockedBy if p.blockedBy is not None
                            else p.stageGoal)
                elif kv[0]=='--scan':
                    missingProjects,newProjects,suggestedLinks=\
                        d.projects.scanProjects()
                    print('Missing',len(missingProjects))
                    print('----------------')
                    for p in missingProjects:
                        print(p.title,':',p.series,':',p.documentLocation)
                    print('\nNew',len(newProjects))
                    print('----------------')
                    for p in newProjects:
                        print(p.title,':',p.series,':',p.documentLocation)
                    print('\nSuggested Links',len(suggestedLinks))
                    print('----------------')
                    for p,location in suggestedLinks:
                        print(p.title,':',p.series,':',location)
                elif kv[0]=='--open':
                    p=d.projects.getByName(kv[1]).open()
                else:
                    print('ERR: unknown argument "'+kv[0]+'"')
            else:
                print('ERR: unknown argument "'+arg+'"')
    if printhelp:
        print('Usage:')
        print('  writersDashboard.py [options]')
        print('Options:')
        print('   --ui ................. launch the user interface')
        print('   --dump ............... dump all current projects')
        print('   --scan ............... scan the projects location for new/broken/linked projects') # noqa: E501 # pylint: disable=line-too-long
        print('   --top[=n] ............ get a quick and simple todo list of n items (default=4)') # noqa: E501 # pylint: disable=line-too-long
        print('   --open=project ....... open the main file associated with a project') # noqa: E501 # pylint: disable=line-too-long


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
