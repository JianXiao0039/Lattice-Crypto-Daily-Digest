param(
    [string]$Week,
    [string]$FromDate,
    [string]$ToDate
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $RepoRoot

$args = @("-m", "lattice_digest.weekly")

if ($Week) {
    $args += @("--week", $Week)
} elseif ($FromDate -and $ToDate) {
    $args += @("--from-date", $FromDate, "--to-date", $ToDate)
} else {
    $today = Get-Date
    $culture = [System.Globalization.CultureInfo]::InvariantCulture
    $calendar = $culture.Calendar
    $weekNumber = $calendar.GetWeekOfYear(
        $today,
        [System.Globalization.CalendarWeekRule]::FirstFourDayWeek,
        [DayOfWeek]::Monday
    )
    $Week = "{0}-W{1:D2}" -f $today.Year, $weekNumber
    $args += @("--week", $Week)
}

& python @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "Weekly brief generation failed."
    exit $LASTEXITCODE
}
