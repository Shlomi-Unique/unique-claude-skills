# Fixes Hebrew drafts in Outlook: right-to-left and Arial, in one run.
# Usage:  powershell -ExecutionPolicy Bypass -File ".\fix-rtl-drafts.ps1" -SubjectContains "[הדגמה]"
# Touches only drafts whose subject contains -SubjectContains. Drafts already fixed are skipped.
param([string]$SubjectContains = "[הדגמה]")

$ol = New-Object -ComObject Outlook.Application
$ns = $ol.GetNamespace("MAPI")
$fixed = 0; $skipped = 0
$wrapOpen = '<div dir="rtl" style="direction:rtl;text-align:right;font-family:Arial,sans-serif">'

foreach ($store in $ns.Stores) {
    try { $drafts = $store.GetDefaultFolder(16) } catch { continue }   # 16 = Drafts
    foreach ($m in @($drafts.Items)) {
        if ($m.Class -ne 43) { continue }                              # 43 = MailItem
        if (-not $m.Subject -or -not $m.Subject.Contains($SubjectContains)) { continue }
        $h = $m.HTMLBody
        if ($h.Contains('data-rtl-fixed')) { $skipped++; continue }
        # Paragraphs: right-to-left and right-aligned
        $h = [regex]::Replace($h, '<p(?=[\s>])', '<p dir="rtl" align="right" style="direction:rtl;text-align:right;font-family:Arial,sans-serif"')
        # Wrap the whole body so any loose text follows too
        $h = [regex]::Replace($h, '(<body[^>]*>)', ('$1' + $wrapOpen.Replace('<div ', '<div data-rtl-fixed="1" ')), 1)
        $h = [regex]::Replace($h, '</body>', '</div></body>', 1)
        $m.HTMLBody = $h
        $m.Save()
        $fixed++
        Write-Output ("fixed: " + $m.Subject)
    }
}
Write-Output ("Done. fixed=" + $fixed + " already-fixed=" + $skipped)
