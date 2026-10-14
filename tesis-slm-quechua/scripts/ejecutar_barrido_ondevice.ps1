# Orquesta el barrido experimental on-device, un escenario por proceso.
#
# Reinicializar el motor LiteRT dentro del mismo proceso provoca un SIGSEGV
# unos segundos despues de que `cleanUp` confirma la liberacion del modelo. Por
# eso cada escenario se ejecuta en una sesion limpia de la app: se lanza por
# deep link con auto-arranque, se espera a que termine y se mata el proceso
# antes del siguiente. Como efecto secundario deseable, ningun escenario hereda
# el estado de memoria ni la cache del anterior.
#
# Uso:
#   powershell -File scripts/ejecutar_barrido_ondevice.ps1
#   powershell -File scripts/ejecutar_barrido_ondevice.ps1 -Escenarios E2,E3

param(
    [string[]]$Escenarios = @("E1", "E2", "E3"),
    [string]$Dispositivo = "emulator-5554",
    [string]$Modelo = "Qwen2.5-3B Base (E1 Control - E2 con RAG)",
    [int]$TimeoutMinutosPorEscenario = 90
)

# adb escribe en stderr incluso cuando termina con exito ("N files pulled").
# Con ErrorActionPreference = Stop, PowerShell 5.1 convierte esa salida en un
# NativeCommandError terminante y aborta el barrido a mitad de camino.
$ErrorActionPreference = "Continue"

# Invocado con `powershell -File`, un `-Escenarios E2,E3` llega como un unico
# string "E2,E3" en vez de como array: sin esta normalizacion el bucle iteraria
# una sola vez con un codigo de escenario inexistente.
$Escenarios = $Escenarios |
    ForEach-Object { $_ -split ',' } |
    ForEach-Object { $_.Trim().ToUpper() } |
    Where-Object { $_ }

$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$paquete = "com.google.aiedge.gallery"
$dirApp = "/storage/emulated/0/Android/data/$paquete/files"
$destinoLocal = "D:\Proyectos\Seminario\tesis-slm-quechua\results"

if (-not (Test-Path $destinoLocal)) { New-Item -ItemType Directory -Path $destinoLocal | Out-Null }

# El nombre del modelo viaja en la URI: hay que codificarlo porque lleva
# espacios y parentesis.
$modeloUri = [System.Uri]::EscapeDataString($Modelo)

function Contar-Mediciones([string]$archivo) {
    $salida = & $adb -s $Dispositivo shell "grep -o '\""escenario\""' $archivo 2>/dev/null | wc -l"
    $n = 0
    [int]::TryParse(($salida -replace '\s', ''), [ref]$n) | Out-Null
    return $n
}

Write-Output "=== Barrido on-device: $($Escenarios -join ', ') ==="
& $adb -s $Dispositivo shell svc power stayon true | Out-Null

foreach ($esc in $Escenarios) {
    $archivo = "$dirApp/benchmark_ondevice_$esc.json"
    Write-Output ""
    Write-Output "--- $esc ---"

    & $adb -s $Dispositivo shell "rm -f $archivo" | Out-Null
    & $adb -s $Dispositivo shell "am force-stop $paquete" | Out-Null
    Start-Sleep -Seconds 5

    $uri = "com.google.ai.edge.gallery://evaluacion/$modeloUri" + "?escenario=$esc&auto=1"
    & $adb -s $Dispositivo shell "am start -a android.intent.action.VIEW -d '$uri'" | Out-Null

    $inicio = Get-Date
    $previo = -1
    $estancado = 0

    while ($true) {
        Start-Sleep -Seconds 60

        $vivo = (& $adb -s $Dispositivo shell "pidof $paquete") -replace '\s', ''
        $n = Contar-Mediciones $archivo

        if ($n -ne $previo) {
            $mins = [math]::Round(((Get-Date) - $inicio).TotalMinutes, 1)
            Write-Output ("  {0,3}/100  ({1} min)" -f $n, $mins)
            $previo = $n
            $estancado = 0
        } else {
            $estancado++
        }

        if ($n -ge 100) { Write-Output "  $esc completo"; break }

        if (-not $vivo) {
            Write-Output "  ATENCION: el proceso murio con $n/100 mediciones"
            break
        }
        if (((Get-Date) - $inicio).TotalMinutes -gt $TimeoutMinutosPorEscenario) {
            Write-Output "  ATENCION: timeout con $n/100 mediciones"
            break
        }
        # Sin avance durante 15 minutos: se considera bloqueado.
        if ($estancado -ge 15) {
            Write-Output "  ATENCION: sin avance en 15 min, con $n/100 mediciones"
            break
        }
    }

    $local = "$destinoLocal\benchmark_ondevice_$esc.json"
    & $adb -s $Dispositivo pull $archivo $local | Out-Null
    if (Test-Path $local) {
        Write-Output ("  recuperado: {0:N0} KB" -f ((Get-Item $local).Length / 1KB))
    } else {
        Write-Output "  ATENCION: no se pudo recuperar $local"
    }

    & $adb -s $Dispositivo shell "am force-stop $paquete" | Out-Null
    Start-Sleep -Seconds 5
}

Write-Output ""
Write-Output "=== Archivos recuperados ==="
Get-ChildItem "$destinoLocal\benchmark_ondevice_*.json" |
    Select-Object Name, @{n = 'KB'; e = { [math]::Round($_.Length / 1KB, 0) } }
Write-Output ""
Write-Output "Combina y calcula metricas con:"
Write-Output "  python scripts/fase4_metricas_ondevice.py --combinar"
