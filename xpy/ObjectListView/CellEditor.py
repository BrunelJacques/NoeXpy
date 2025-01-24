# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         CellEditor.py
# Author:       Phillip Piper
# Created:      3 April 2008
# Copyright:    (c) 2008 by Phillip Piper, 2008
# License:      wxWindows license
#----------------------------------------------------------------------------
# Change log:
# 2009/06/09  JPP   All cell editors start life 0 sized to prevent flickering
# 2008/05/26  JPP   Fixed pyLint annoyances
# 2008/04/04  JPP   Initial version complete
#----------------------------------------------------------------------------
# To do:
# - there has to be a better DateTimeEditor somewhere!!

"""
The *CellEditor* module provides some editors for standard types that can be installed
in an *ObjectListView*. It also provides a *Registry* that maps between standard types
and functions that will create editors for that type.

Cell Editors

    A cell editor can be any subclass of wx.Window provided that it supports the
    following protocol:

    SetValue(self, value)
        The editor should show the given value for editing

    GetValue(self)
        The editor should return the value that it holds. Return None to indicate
        an invalid value. The returned value should be of the correct type, i.e.
        don't return a string if the editor was registered for the bool type.

    The editor should invoke FinishCellEdit() on its parent ObjectListView when it
    loses focus or when the user commits the change by pressing Return or Enter.

    The editor should invoke CancelCellEdit() on its parent ObjectListView when
    the user presses Escape.

Editor Registry

    The editor registry remembers a function that will be called to create
    an editor for a given type.
"""

__author__ = "Phillip Piper"
__date__ = "3 May 2008"

import datetime
import wx
import wx.adv
validator = wx.Validator

# Editor Registry

_cellEditorRegistrySingleton = None

def GetValideLigne(track):
    # permet de quitter la ligne ou pas selon la validité de la saisie testée par ValideLigne en sortie de cellEditor
    descend = 1
    if track:
        track.vierge = False
        # création d'un message par défaut
        if not hasattr(track,'messageRefus'):
            track.messageRefus = "Il faut revoir la saisie,\n\n la ligne n'est pas valide\ndixit CellEditor.GetValideLigne"
        if not hasattr(track,'valide'):
            track.valide = True
        if not track.valide:
            if track.noSaisie == False:
                wx.MessageBox(track.messageRefus,"Ligne invalide",style=wx.ICON_ERROR)
            descend = 0
    return descend

def EnterAction(event):
    # Touche enter on détourne l'usage pour un équivalent tab sauf en fin de ligne on passe à la suivante
    olv = event.EventObject.Parent
    try:
        row, col = olv.cellBeingEdited
    except: return
    olv.error = None
    olv.FinishCellEdit()
    if olv.error :
        go = 0
    else:
        go = 1
    # avancement d'une colonne
    for ix in range(col+go,olv.ColumnCount):
        # saute une cellule non éditable
        if olv.columns[ix].isEditable:
            olv._PossibleStartCellEdit(row,ix)
            break
        col = ix
    # fin de ligne, on passe à la suivante si la ligne est valide
    if col == olv.ColumnCount - 1:
        # ajout éventuel d'une nouvelle ligne
        if row == len(olv.innerList)-1:
            if olv.autoAddRow:
                if hasattr(olv.innerList[row],'valide') and olv.innerList[row].valide == True:
                    olv.AutoAddRow()
                    olv.RepopulateList()
            else:
                row -=1
        track = olv.innerList[row]
        row += GetValideLigne(track)
        coldefn = olv.GetPrimaryColumn()
        col = olv.columns.index(coldefn)-1
        olv._SelectAndFocus(row)
    return

def UpDownAction(event):
    # Touche Up et Down changent de ligne
    keyup = event.GetKeyCode() in (wx.WXK_UP,wx.WXK_NUMPAD_UP)
    olv = event.EventObject.Parent
    row, col = olv.cellBeingEdited
    olv.FinishCellEdit()
    track = olv.GetSelectedObject()
    if row != len(olv.innerList)-1 and not keyup:
        # on passe à la ligne suivante
        row += GetValideLigne(track)
    elif row != 0 and keyup:
        row -= GetValideLigne(track)
    olv._SelectAndFocus(row)
    olv._PossibleStartCellEdit(row, col)
    return

def ShiftTabAction(event):
    # Gestion pour éditeur date qui ne gère pas la tabulation
    olv = event.EventObject.Parent
    row, col = olv.cellBeingEdited
    olv.FinishCellEdit()
    if olv.columns[col-1].isEditable:
        olv._PossibleStartCellEdit(row, col - 1)
    else:
        for ix in range(col-1,-1,-1):
            # saute une cellule non éditable
            if olv.columns[ix].isEditable:
                olv._PossibleStartCellEdit(row,ix)
                break
    return

def EscapeAction(event):
    olv = event.EventObject.Parent
    if hasattr(event.EventObject.GrandParent, 'OnEditStarted'):
        row, col = olv.cellBeingEdited
        track = olv.GetObjectAt(row)
        if track.oldValue:
            event.EventObject.SetValue(track.oldValue)
    olv.FinishCellEdit()
    if hasattr(event.EventObject.GrandParent, 'OnEditStarted'):
        GetValideLigne(track)
    return

def FunctionKeys(event):
    olv = event.EventObject.Parent
    row, col = olv.cellBeingEdited
    if hasattr(event.EventObject.GrandParent, 'OnEditFunctionKeys'):
        olv.FinishCellEdit()
        olv.cellBeingEdited = (row, col)
        event.EventObject.GrandParent.OnEditFunctionKeys(event)
        olv._PossibleStartCellEdit(row, col)
        #EnterAction(event, finish=False)
    else:
        wx.MessageBox(u"Touches de fonctions non implémentées")
    event.Skip()
    return

def OnChar(editor, event):

    if event.GetModifiers() != 0 and event.GetModifiers() != wx.MOD_SHIFT:
        # passe les alt ctrl et altgr
        event.Skip()
        return

    if event.GetKeyCode() >= wx.WXK_F1 and event.GetKeyCode() <= wx.WXK_F12:
        FunctionKeys(event)
        return

    if event.GetKeyCode() == 61:
        # touche égal
        FunctionKeys(event)
        return

    # le shift Tab doit sauter les non éditables
    if event.GetKeyCode() == wx.WXK_TAB and  event.GetModifiers() == wx.MOD_SHIFT:
            ShiftTabAction(event)
            return

    if type(editor).__name__ in ('DateEditor','ChoiceEditor','ComboEditor','BoleanEditor','CheckEditor'):
        # pour ces editor particuliers on traite les comportements spécifiques :tab(surtout pour date)
        if event.GetKeyCode() == wx.WXK_TAB:
            if event.GetModifiers() == wx.MOD_SHIFT:
                ShiftTabAction(event)
            elif event.GetModifiers() == 0:
                EnterAction(event)
            return
        if event.GetKeyCode() in (wx.WXK_UP, wx.WXK_DOWN):
            event.Skip()
            return

    if event.GetKeyCode() == wx.WXK_TAB and event.GetModifiers() == 0:
        # pour gérer le tab en fin de ligne on le ramène à Enter
        EnterAction(event)
        return

    if event.GetKeyCode() in [wx.WXK_CANCEL, wx.WXK_TAB, wx.WXK_BACK, wx.WXK_DELETE, wx.WXK_HOME,
                              wx.WXK_END,wx.WXK_LEFT, wx.WXK_RIGHT,]:
        event.Skip()
        return

    #EditKeysPerso = [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER,wx.WXK_ESCAPE,wx.WXK_UP, wx.WXK_DOWN ]

    if event.GetKeyCode() in (wx.WXK_UP,wx.WXK_NUMPAD_UP,wx.WXK_DOWN,wx.WXK_NUMPAD_DOWN):
        UpDownAction(event)
        return

    if event.GetKeyCode() in (wx.WXK_RETURN,wx.WXK_NUMPAD_ENTER):
        EnterAction(event)
        return

    if event.GetKeyCode() == (wx.WXK_ESCAPE):
        EscapeAction(event)
        return
    event.Skip()
    return

def CellEditorRegistry():
    """
    Return the registry that is managing type to creator functions
    """
    global _cellEditorRegistrySingleton

    if _cellEditorRegistrySingleton is None:
        _cellEditorRegistrySingleton = EditorRegistry()

    return _cellEditorRegistrySingleton


class EditorRegistry:

    """
    An *EditorRegistry* manages a mapping of types onto creator functions.

    When called, creator functions will create the appropriate kind of cell editor
    """

    def __init__(self):
        self.typeToFunctionMap = {}

        # Standard types and their creator functions
        self.typeToFunctionMap[str] = self._MakeStringEditor
        self.typeToFunctionMap[bool] = self._MakeCheckEditor
        #self.typeToFunctionMap[bool] = self._MakeBoolEditor
        self.typeToFunctionMap[int] = self._MakeIntegerEditor
        #self.typeToFunctionMap[int] = self._MakeLongEditor
        self.typeToFunctionMap[float] = self._MakeFloatEditor
        self.typeToFunctionMap[wx.DateTime] = self._MakeDateEditor
        self.typeToFunctionMap[datetime.datetime] = self._MakeDateTimeEditor
        self.typeToFunctionMap[datetime.date] = self._MakeDateTimeEditor
        self.typeToFunctionMap[datetime.time] = self._MakeTimeEditor

    def GetCreatorFunction(self, aValue):
        """
        Return the creator function that is register for the type of the given value.
        Return None if there is no registered function for the type.
        """
        return self.typeToFunctionMap.get(type(aValue), None)

    def RegisterCreatorFunction(self, aType, aFunction):
        """
        Register the given function to be called when we need an editor for the given type.

        The function must accept three parameter: an ObjectListView, row index, and subitem index.
        It should return a wxWindow that is parented on the listview, and that responds to:

           - SetValue(newValue)

           - GetValue() to return the value shown in the editor

        """
        self.typeToFunctionMap[aType] = aFunction

    #-------------------------------------------------------------------------
    # Creator functions for standard types

    @staticmethod
    def _MakeStringEditor(olv, rowIndex, subItemIndex):
        return BaseCellTextEditor(olv,rowIndex,subItemIndex)

    @staticmethod
    def _MakeBoolEditor(olv, rowIndex, subItemIndex):
        return BooleanEditor(olv,rowIndex, subItemIndex)

    @staticmethod
    def _MakeIntegerEditor(olv, rowIndex, subItemIndex):
        return IntEditor(olv,rowIndex, subItemIndex, validator=NumericValidator())

    @staticmethod
    def _MakeLongEditor(olv, rowIndex, subItemIndex):
        return LongEditor(olv,rowIndex, subItemIndex, validator=NumericValidator())

    @staticmethod
    def _MakeFloatEditor(olv, rowIndex, subItemIndex):
        return FloatEditor(olv,rowIndex, subItemIndex, validator=NumericValidator("0123456789-+eE."))

    @staticmethod
    def _MakeDateTimeEditor(olv, rowIndex, subItemIndex):
        dte = DateTimeEditor(olv,rowIndex, subItemIndex, validator=NumericValidator("0123456789/-"))
        column = olv.columns[subItemIndex]
        if isinstance(column.stringConverter, str):
            dte.formatString = column.stringConverter
        return dte

    @staticmethod
    def _MakeDateEditor(olv, rowIndex, subItemIndex):
        dte = DateEditor(olv,rowIndex, subItemIndex, validator=NumericValidator("0123456789/-"))
        #dte = DateEditor(olv, style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY | wx.WANTS_CHARS)
        return dte

    @staticmethod
    def _MakeCheckEditor(olv, rowIndex, subItemIndex):
        return CheckEditor(olv,rowIndex, subItemIndex)

    @staticmethod
    def _MakeTimeEditor(olv, rowIndex, subItemIndex):
        editor = TimeEditor(olv,rowIndex, subItemIndex)

        column = olv.columns[subItemIndex]
        if isinstance(column.stringConverter, str):
            editor.formatString = column.stringConverter

        return editor

#==================== Cell editors ===================================================================

class BooleanEditor(wx.Choice):
    """This is a simple editor to edit a boolean value that can be used in an
    ObjectListView"""

    def __init__(self, olv,row,col, **kwargs):
        kwargs["choices"] = ["Oui", "Non"]
        wx.Choice.__init__(self, olv, **kwargs)
        olv.editor = {col: self}
        self.Bind(wx.EVT_CHAR_HOOK, self._OnChar)
        self.row = row
        self.col = col
    def _OnChar(self, event):
        OnChar(self, event)

    def GetValue(self):
        "Get the value from the editor"
        return self.GetSelection() == 0

    def SetValue(self, value):
        "Put a new value into the editor"
        if value:
            self.Select(0)
        else:
            self.Select(1)

class CheckEditor(wx.CheckBox):
    def __init__(self, olv,row,col,**kwargs):
        wx.CheckBox.__init__(self,olv)
        self.SetValue(False)
        self.Bind(wx.EVT_CHAR_HOOK, self._OnChar)
        olv.editor = {col: self}
        self.row = row
        self.col = col
    def _OnChar(self, event):
        OnChar(self,event)

class ChoiceEditor(wx.Choice):
    # doit être géré à l'entrée de la cellule par SetItems Personnalisé
    def __init__(self,olv,row,col, **kwargs):
        if col in olv.dicChoices.keys():
            kwargs['choices']=olv.dicChoices[col]
        wx.Choice.__init__(self,olv, **kwargs)
        self.SetSelection(0)
        olv.editor = {col:self}
        self.row = row
        self.col = col
        self.Bind(wx.EVT_CHAR_HOOK, self._OnChar)

    def _OnChar(self, event):
        OnChar(self, event)

    def GetValue(self):
        "Get the value from the editor"
        try:
            val = self.GetString(self.GetSelection())
        except:
            val = None
        return val

    def SetValue(self,value):
        if value in self.GetItems():
            self.SetSelection(self.GetItems().index(str(value)))
        else:
            for item in self.GetItems():
                if str(value) == str(item)[:len(str(value))]:
                    self.SetSelection(self.GetItems().index(item))
                    break
        return

class ComboEditor(wx.ComboBox):
    # doit être géré à l'entrée de la cellule par SetItems Personnalisé
    def __init__(self, olv,row,col, **kwargs):
        if col in olv.dicChoices.keys():
                kwargs['choices']=olv.dicChoices[col]
        wx.ComboBox.__init__(self, olv,style = wx.TE_PROCESS_ENTER| wx.TE_PROCESS_TAB, **kwargs)
        olv.editor = {col:self}
        self.row = row
        self.col = col
        self.Bind(wx.EVT_CHAR_HOOK, self._OnChar)

    def _OnChar(self, event):
        OnChar(self, event)

    def SetValue(self,value):
        if value in self.GetItems():
            self.SetSelection(self.GetItems().index(str(value)))
        else:
            for item in self.GetItems():
                if str(value) == str(item)[:len(str(value))]:
                    self.SetSelection(self.GetItems().index(item))
                    break
        return

class DateEditor(wx.adv.DatePickerCtrl):
    """
    This control uses standard datetime.
    wx.DatePickerCtrl works only with wx.DateTime, but they are strange beasts.
    wx.DataTime use 0 indexed months, i.e. January==0 and December==11.
    """
    def __init__(self, olv,row,col, **kwargs):
        wx.adv.DatePickerCtrl.__init__(self,olv, **kwargs)
        self.SetValue(None)
        olv.editor = {col:self}
        self.Bind(wx.EVT_CHAR_HOOK, self._OnChar)
        self.row = row
        self.col = col

    def _OnChar(self, event):
        OnChar(self,event)

    def SetValue(self, value):
        if isinstance(value,(datetime.date,datetime.datetime)):
            dt = wx.DateTime(value.day, value.month-1 , value.year)
        elif isinstance(value,wx.DateTime):
            dt = wx.DateTime(value.GetDay(), value.GetMonth(), value.GetYear())
        else:
            dt = wx.DateTime.Today()
        wx.adv.DatePickerCtrl.SetValue(self, dt)

    def GetValue(self):
        "Get the value from the editor"
        dt = wx.adv.DatePickerCtrl.GetValue(self)
        #dt.Month += 1
        #return datetime.date(dt.Year, dt.Month , dt.Day)
        return dt

# Base Texte et ses dérivés
class BaseCellTextEditor(wx.TextCtrl):
    """This is a base text editor for text-like editors used in an ObjectListView"""
    def __init__(self, olv, row, subItemIndex, **kwargs):
        style = wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB
        self.error = None
        self.row = row
        self.col = subItemIndex
        # Allow for odd case where parent isn't an ObjectListView
        if hasattr(olv, "columns"):
            if olv.HasFlag(wx.LC_ICON):
                style |= (wx.TE_CENTRE | wx.TE_MULTILINE)
            else:
                style |= olv.columns[subItemIndex].GetAlignmentForText()
        wx.TextCtrl.__init__(self, olv, style=style, **kwargs)
        # With the MULTILINE flag, the text control always has a vertical
        # scrollbar, which looks stupid. I don't know how to get rid of it.
        # This doesn't do it:
        # self.ToggleWindowStyle(wx.VSCROLL)
        self.Bind(wx.EVT_CHAR_HOOK, self._OnChar)

    def _OnChar(self, event):
        OnChar(self, event)

class IntEditor(BaseCellTextEditor):
    """This is a text editor for integers for use in an ObjectListView"""

    def GetValue(self):
        "Get the value from the editor"
        s = wx.TextCtrl.GetValue(self).strip()
        try:
            return int(s)
        except ValueError:
            return None

    def SetValue(self, value):
        "Put a new value into the editor"
        if isinstance(value, int):
            value = repr(value)
        wx.TextCtrl.SetValue(self, value)

class LongEditor(BaseCellTextEditor):
    """This is a text editor for long values for use in an ObjectListView"""

    def GetValue(self):
        "Get the value from the editor"
        s = wx.TextCtrl.GetValue(self).strip()
        try:
            return int(s)
        except ValueError:
            return None

    def SetValue(self, value):
        "Put a new value into the editor"
        if isinstance(value, int):
            value = repr(value)
        wx.TextCtrl.SetValue(self, value)

class FloatEditor(BaseCellTextEditor):
    """This is a text editor for floats for use in an ObjectListView.

    Because of the trouble of precisely converting floats to strings,
    this editor sometimes behaves a little strangely."""

    def GetValue(self):
        "Get the value from the editor"
        s = wx.TextCtrl.GetValue(self).strip()
        try:
            return float(s)
        except ValueError:
            return None

    def SetValue(self, value):
        "Put a new value into the editor"
        if isinstance(value, (float,int)):
            value = repr(round(value,6))
        wx.TextCtrl.SetValue(self, value)

class DateTimeEditor(BaseCellTextEditor):
    """
    A DateTimeEditor allows the user to enter a date/time combination, where the time is optional
    and many formats of date and time are allowed.

    The control accepts these date formats (in all cases, the year can be only 2 digits):
      - '31/12/2008'
      - '2008/12/31'
      - '12/31/2008'
      - '31 December 2008'
      - '31 Dec 2008'
      - 'Dec 31 2008'
      - 'December 31 2008'

    Slash character can also be '-' or ' '. Consecutive whitespace are collapsed.

    The implementation uses a brute force approach to parsing the data.
    """
    # Acceptable formats:
    # '31/12/2008', '2008-12-31', '31/12/08', '3112', '311208'

    def __init__(self, *args, **kwargs):
        BaseCellTextEditor.__init__(self, *args, **kwargs)
        self.formatString = "%X %x"

    def SetValue(self, value):
        "Put a new value into the editor"
        if isinstance(value, (datetime.date)):
            value = value.strftime(self.formatString)[-10:]
            self.formatString = "%x"
        if isinstance(value, (datetime.datetime)):
            value = value.strftime(self.formatString)
        wx.TextCtrl.SetValue(self, value)

    def GetValue(self):
        "Get the value from the editor"
        s = wx.TextCtrl.GetValue(self)
        return DateToDatetime(self,s)

class TimeEditor(BaseCellTextEditor):
    """A text editor that expects and return time values"""

    # Acceptable formats: '23:59', '11:59pm', '11pm'
    STD_TIME_FORMATS = ['%X', '%H:%M', '%I:%M %p', '%I %p']

    def __init__(self, *args, **kwargs):
        BaseCellTextEditor.__init__(self, *args, **kwargs)
        self.formatString = "%X"

    def SetValue(self, value):
        "Put a new value into the editor"
        value = value or ""
        if isinstance(value, datetime.time):
            value = value.strftime(self.formatString)
        wx.TextCtrl.SetValue(self, value)

    def GetValue(self):
        "Get the value from the editor"
        s = wx.TextCtrl.GetValue(self).strip()
        fmts = self.STD_TIME_FORMATS[:]
        if self.formatString not in fmts:
            fmts.insert(0, self.formatString)
        for fmt in fmts:
            try:
                dt = datetime.datetime.strptime(s, fmt)
                return dt.time()
            except ValueError:
                pass

        return None

#==================== Cell validators =================================================================

class NumericValidator(wx.PyValidator):
    """This validator only accepts numeric keys"""

    def __init__(self, acceptableChars="0123456789+-"):
        wx.Validator.__init__(self)
        self.acceptableChars = acceptableChars
        self.acceptableCodes = [ord(x) for x in self.acceptableChars]
        self.Bind(wx.EVT_CHAR, self._OnChar)

    def Clone(self):
        "Make a new copy of this validator"
        return NumericValidator(self.acceptableChars)

    def _OnChar(self, event):
        # complément du bind de BaseCellTextEditor, rejet des lettres accept les chiffres
        if event.GetModifiers() != 0 and event.GetModifiers() != wx.MOD_SHIFT:
            # passe les alt ctrl et altgr
            event.Skip()
            return

        if event.GetKeyCode() in self.acceptableCodes:
            # accepte les acceptables
            event.Skip()
            return

        if event.GetKeyCode() >= 32 and event.GetKeyCode() != 127 and event.GetKeyCode() < 256:
            # bloque les ascii non aceptables, interromp le traitement
            wx.Bell()
            return
        event.Skip()


def DateToDatetime(parent,date):
    # après une saisie de date, la transforme en datetime
    error = None
    dtdate = None
    date = date.strip()
    if date == '':
        return ''
    tplansi = date.split('-')
    tpldate = date.split('/')
    try:
        # saisie ansi
        if len(tplansi)==3:
            if int(tplansi[0]) <50:
                tplansi[0] = "20"+tplansi[0]
            if int(tplansi[0]) <100:
                tplansi[0] = "19"+tplansi[0]
            dtdate = datetime.date(int(tplansi[0]),int(tplansi[1]),int(tplansi[2]))
        # saisie française avec '/'
        elif len(tpldate) == 3:
            if int(tpldate[2]) < 40:
                tpldate[2] = "20" + tpldate[2]
            if int(tpldate[2]) < 100:
                tpldate[2] = "19" + tpldate[2]
            dtdate = datetime.date(int(tpldate[2]), int(tpldate[1]), int(tpldate[0]))
        # saisie française sans séparateurs
        elif len(date) == 4:
            dtdate = datetime.date(datetime.date.today().year,int(date[2:4]), int(date[:2]))
        elif len(date) == 6:
            dtdate = datetime.date(2000+int(date[4:6]), int(date[2:4]), int(date[:2]))
        elif len(date) == 8:
            dtdate = datetime.date(int(date[4:8]), int(date[2:4]), int(date[:2]))
        else: error = "Date saisie non reconnue: '%s'"%date
    except:
        import sys
        error = "Erreur:", sys.exc_info()[1]
    if error:
        parent.error = error
    return dtdate

# ============== Auto complete controls =========================================

def MakeAutoCompleteTextBox(olv, columnIndex, maxObjectsToConsider=10000):
    """
    Return a TextCtrl that lets the user choose from all existing values in this column.
    Do not call for large lists
    """
    col = olv.columns[columnIndex]
    # THINK: We could make this time based, i.e. it escapes after 1 second.
    maxObjectsToConsider = min(maxObjectsToConsider, olv.GetItemCount())
    options = set(col.GetStringValue(olv.GetObjectAt(i)) for i in range(maxObjectsToConsider))
    tb = BaseCellTextEditor(olv, columnIndex)
    AutoCompleteHelper(tb, list(options))
    return tb


def MakeAutoCompleteComboBox(olv, columnIndex, maxObjectsToConsider=10000):
    """
    Return a ComboBox that lets the user choose from all existing values in this column.
    Do not call for large lists
    """
    col = olv.columns[columnIndex]
    maxObjectsToConsider = min(maxObjectsToConsider, olv.GetItemCount())
    options = set(col.GetStringValue(olv.GetObjectAt(i)) for i in range(maxObjectsToConsider))
    cb = wx.ComboBox(olv, choices=list(options),
                     style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_PROCESS_ENTER)
    AutoCompleteHelper(cb)
    return cb

class AutoCompleteHelper(object):
    """
    This class operates on a text control or combobox, and automatically completes the
    text typed by the user from a list of entries in a given list.

    """

    def __init__(self, control, possibleValues=None):
        self.control = control
        self.lastUserEnteredString = self.control.GetValue()
        self.control.Bind(wx.EVT_TEXT, self._OnTextEvent)
        if isinstance(self.control, wx.ComboBox):
            self.possibleValues = self.control.GetStrings()
        else:
            self.possibleValues = possibleValues or []
        self.lowerCasePossibleValues = [x.lower() for x in self.possibleValues]

    def _OnTextEvent(self, evt):
        evt.Skip()
        # After the SetValue() we want to ignore this event. If we get this event
        # and the value hasn't been modified, we know it was a SetValue() call.
        if hasattr(self.control, "IsModified") and not self.control.IsModified():
            return

        # If the text has changed more than the user just typing one letter,
        # then don't try to autocomplete it.
        if len(evt.GetString()) != len(self.lastUserEnteredString) + 1:
            self.lastUserEnteredString = evt.GetString()
            return

        self.lastUserEnteredString = evt.GetString()
        s = evt.GetString().lower()
        for i, x in enumerate(self.lowerCasePossibleValues):
            if x.startswith(s):
                self._AutocompleteWith(self.possibleValues[i])
                break

    def _AutocompleteWith(self, newValue):
        """Suggest the given value by autocompleting it."""
        # GetInsertionPoint() doesn't seem reliable under linux
        insertIndex = len(self.control.GetValue())
        self.control.SetValue(newValue)
        if isinstance(self.control, wx.ComboBox):
            self.control.SetMark(insertIndex, len(newValue))
        else:
            # Seems that under linux, selecting only seems to work here if we do it
            # outside of the text event
            wx.CallAfter(self.control.SetSelection, insertIndex, len(newValue))
