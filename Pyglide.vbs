Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /k python ""C:\PyGlide\pyglide_ui\main.py""", 0, False
Set WshShell = Nothing
