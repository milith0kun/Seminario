Add-Type -AssemblyName System.Drawing
[Windows.Globalization.Language, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null

$lang = [Windows.Globalization.Language]::new('es')
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
if (-not $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }

Get-ChildItem scratch/slides_objetivos/slide_*.png | Sort-Object { [int]($_.BaseName -replace '\D') } | ForEach-Object {
    $name = $_.Name
    $fileTask = [Windows.Storage.StorageFile]::GetFileFromPathAsync($_.FullName)
    $asTask = [WindowsRuntimeSystemExtensions]::AsTask($fileTask)
    $file = $asTask.GetAwaiter().GetResult()
    
    $streamTask = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    $stream = [WindowsRuntimeSystemExtensions]::AsTask($streamTask).GetAwaiter().GetResult()
    
    $decoderTask = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
    $decoder = [WindowsRuntimeSystemExtensions]::AsTask($decoderTask).GetAwaiter().GetResult()
    
    $bmpTask = $decoder.GetSoftwareBitmapAsync()
    $bmp = [WindowsRuntimeSystemExtensions]::AsTask($bmpTask).GetAwaiter().GetResult()
    
    $ocrTask = $engine.RecognizeAsync($bmp)
    $result = [WindowsRuntimeSystemExtensions]::AsTask($ocrTask).GetAwaiter().GetResult()
    
    Write-Host "=== $name ==="
    Write-Host $result.Text
}
