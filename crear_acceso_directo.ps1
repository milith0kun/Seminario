$WshShell = New-Object -ComObject WScript.Shell
$desktop = [System.Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$desktop\Iniciar Emulador Android.lnk")
$Shortcut.TargetPath = "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe"
$Shortcut.Arguments = "-avd Medium_Phone_API_36.1"
$Shortcut.WorkingDirectory = "$env:LOCALAPPDATA\Android\Sdk\emulator"
$Shortcut.Save()
Write-Host "Acceso directo creado en el escritorio con exito."
