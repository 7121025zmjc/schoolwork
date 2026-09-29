Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = "D:\2x\windows"
ws.Run """D:\2x\windows\pethospital.exe"" -addr 127.0.0.1:8080", 0, False
