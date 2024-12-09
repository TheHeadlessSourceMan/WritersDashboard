#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This module is for creating ui representational access to backend data
"""
import typing
from paths import URLCompatible, asURL


class UIRepresentation:
    """
    This module is for creating ui representational access to backend data
    """

    EVERYTHING:typing.Dict[str,typing.Any]=\
        {} # {guid:object} of everything the ui knows about

    def __init__(self,uiTemplate:str=None):
        self._uiTemplate:str=uiTemplate
        self._guid:str=None

    def _member_settable(self,memberName:str)->None:
        """
        check to see if a member is considered settable
        """
        m=getattr(self,memberName)
        if isinstance(m,(int,str,float)): # any primative type or derivative
            return True
        elif m.fset is not None:
            return True
        return False

    @property
    def guid(self)->str:
        """
        Guid for the item (will auto-generated itself if needed)
        """
        if self._guid is None:
            import uuid
            self._guid='{'+str(uuid.uuid4())+'}'
        return self._guid
    @guid.setter
    def guid(self,guid:str):
        self._guid=guid

    @property
    def uiTemplate(self)->str:
        """
        always returns a template, even if it has to create one
        """
        if self._uiTemplate is None: # create one from scratch
            self._uiTemplate=[
                f'<div class="{self.__class__.__name__}" id="[[id]]" draggable="true" >'] # noqa: E501 # pylint: disable=line-too-long
            firstElement=None
            doubleclickEvent="this.contentEditable=true;false"
            doneEditEvent="this.contentEditable=false;\
                python('setClassValue',\
                    {'guid':this.parentNode.parentNode.id,'k':this.parentNode.className,'v':this.innerHTML}\
                    );\
                false"
            editLogic=f'ondblclick="{doubleclickEvent}" onfocusout="{doneEditEvent}"' # noqa: E501 # pylint: disable=line-too-long
            for varName in ('name','title'):
                if varName in self.__dict__:
                    firstElement=varName
                    if self._member_settable(varName):
                        self._uiTemplate.append(f'\t<h2 class="{varName}" {editLogic}>\
                            [[{varName}]]\
                            </h2>') # noqa: E501 # pylint: disable=line-too-long
                    else:
                        self._uiTemplate.append(f'\t<h2 class="{varName}">[[{varName}]]</h2>') # noqa: E501 # pylint: disable=line-too-long
                    break
            for varName,var in self.__dict__.items():
                if varName[0]=='_' or varName in (firstElement,'uiTemplate','guid'): # noqa: E501 # pylint: disable=line-too-long
                    continue
                if var.__class__.__module__!='__builtin__': # an object, not a builtin type # noqa: E501 # pylint: disable=line-too-long
                    # TODO: there is probably a way to handle objects
                    continue
                if self._member_settable(varName):
                    self._uiTemplate.append(f'\t<div class="{varName}">\
                        {varName}: <span {editLogic}>[[{varName}]]</span>\
                        </div>')
                else:
                    self._uiTemplate.append(f'\t<div class="{varName}">[[{varName}]]</div>') # noqa: E501 # pylint: disable=line-too-long
            self._uiTemplate.append('</div>')
            self._uiTemplate='\n'.join(self._uiTemplate)
        return self._uiTemplate

    def loadUiTemplate(self,path:URLCompatible)->None:
        """
        load the template
        """
        self._uiTemplate=asURL(path).read()

    def getHtmlControl(self)->str:
        """
        gets an html control for this object based upon the template
        """
        self.EVERYTHING[self.guid]=self
        data=self.uiTemplate.replace('[[id]]',self.guid)
        for k,v in self.__dict__.items():
            k=f'[[{k}]]'
            data=data.replace(k,str(v))
        return data

    def __del__(self):
        """
        unregister this from EVERYTHING global upon delete
        """
        if self._guid is not None:
            if self.guid in self.EVERYTHING:
                del self.EVERYTHING[self.guid]


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
                    print('ERR: unknown argument "'+arg[0]+'"')
            else:
                print('ERR: unknown argument "'+arg+'"')
    if printhelp:
        print('Usage:')
        print('  uiRepresentation.py [options]')
        print('Options:')
        print('   NONE')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
