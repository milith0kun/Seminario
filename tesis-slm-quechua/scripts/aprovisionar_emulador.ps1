# Re-aprovisiona el emulador Android para las mediciones on-device de la tesis.
#
# El emulador solo aplica un aumento de disk.dataPartition.size al arrancar con
# -wipe-data; sin ese paso la particion conserva su tamano anterior. Este script
# reinicia limpio y vuelve a colocar APK, catalogo y pesos.
#
# Uso:
#   powershell -File scripts/aprovisionar_emulador.ps1 [-SkipWipe]

param(
    [switch]$SkipWipe,
    [string]$Avd = "Medium_Phone_API_36.1",
    [int]$MemoriaMB = 6144
)

$ErrorActionPreference = "Stop"

$adb  = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$emu  = "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe"
$raiz = "D:\Proyectos\Seminario"

$apk       = "$raiz\repos-externos\gallery\Android\src\app\build\outputs\apk\debug\app-debug.apk"
$pesos     = "$raiz\tesis-slm-quechua\models\Qwen2.5_Coder_3B_It.litertlm"
$allowlist = "$raiz\repos-externos\gallery\model_allowlists\1_0_19.json"

$paquete = "com.google.aiedge.gallery"
$baseDir = "/storage/emulated/0/Android/data/$paquete/files"
$hash    = "a32e9f082c3fee8adcbe71990eae1eaca3eb0eb9"

# Un directorio por entrada del catalogo: la app deriva el nombre de carpeta
# del nombre del modelo sustituyendo los caracteres no alfanumericos por "_".
$modelos = @(
    "Qwen2_5_3B_Base__E1_Control___E2_con_RAG_",
    "Qwen2_5_3B_Tutor_EIB__E3_Entrenado_"
)

foreach ($f in @($apk, $pesos, $allowlist)) {
    if (-not (Test-Path $f)) { throw "No se encuentra: $f" }
}

$bytes = (Get-Item $pesos).Length
if ($bytes -ne 3433083824) {
    throw "Tamano inesperado de los pesos: $bytes (se esperaban 3433083824 bytes)"
}
Write-Output "[ok] pesos verificados: $bytes bytes"

if (-not $SkipWipe) {
    Write-Output "[1/6] deteniendo emulador"
    & $adb -s emulator-5554 emu kill 2>&1 | Out-Null
    Start-Sleep -Seconds 8

    Write-Output "[2/6] arrancando con -wipe-data (aplica el nuevo tamano de particion)"
    Start-Process -FilePath $emu `
        -ArgumentList '-avd', $Avd, '-gpu', 'host', '-memory', "$MemoriaMB", '-wipe-data' `
        -WindowStyle Minimized
} else {
    Write-Output "[1-2/6] omitido (-SkipWipe)"
}

Write-Output "[3/6] esperando arranque completo"
& $adb -s emulator-5554 wait-for-device
$intentos = 0
while ($intentos -lt 90) {
    $listo = (& $adb -s emulator-5554 shell getprop sys.boot_completed 2>$null)
    if ($listo -match "1") { break }
    Start-Sleep -Seconds 5
    $intentos++
}
if ($intentos -ge 90) { throw "El emulador no completo el arranque" }
Write-Output "[ok] arranque completo"

Write-Output "[4/6] espacio y memoria disponibles"
& $adb -s emulator-5554 shell df -h /data
& $adb -s emulator-5554 shell cat /proc/meminfo | Select-Object -First 1

Write-Output "[5/6] instalando APK"
& $adb -s emulator-5554 install -r $apk

# La app debe haberse ejecutado una vez para que exista su directorio de datos.
& $adb -s emulator-5554 shell am start -n "$paquete/com.google.ai.edge.gallery.MainActivity" | Out-Null
Start-Sleep -Seconds 10
& $adb -s emulator-5554 shell am force-stop $paquete

Write-Output "[6/6] transfiriendo catalogo y pesos (3.4 GB por modelo)"
& $adb -s emulator-5554 shell "mkdir -p $baseDir"
& $adb -s emulator-5554 push $allowlist "$baseDir/model_allowlist.json"

foreach ($m in $modelos) {
    $destino = "$baseDir/$m/$hash"
    Write-Output "  -> $m"
    & $adb -s emulator-5554 shell "mkdir -p '$destino'"
    & $adb -s emulator-5554 push $pesos "$destino/Qwen2.5_Coder_3B_It.litertlm"
}

Write-Output "=== verificacion final ==="
& $adb -s emulator-5554 shell "find $baseDir -name '*.litertlm' -exec ls -l {} \;"
& $adb -s emulator-5554 shell df -h /data
Write-Output "[listo] emulador aprovisionado"
