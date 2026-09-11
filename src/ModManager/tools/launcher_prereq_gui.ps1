# Siedler 6 ModManager - Prerequisite GUI with Language Selection
# Herausgeber: Leopold Walli AI Software Productions

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$repoDir = Split-Path -Parent $PSScriptRoot
$iconPath = Join-Path $PSScriptRoot "assets\icon.ico"

$form = New-Object System.Windows.Forms.Form
$form.Text = "Settlers 6 ModManager - Prerequisite Setup"
$form.Size = New-Object System.Drawing.Size(560, 310)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(22, 27, 34)
$form.ForeColor = [System.Drawing.Color]::FromArgb(240, 246, 252)

if (Test-Path $iconPath) {
    $form.Icon = New-Object System.Drawing.Icon($iconPath)
}

# Header Title
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "👑 The Settlers 6 • Mod & Map Manager"
$lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(241, 196, 15)
$lblTitle.Location = New-Object System.Drawing.Point(24, 16)
$lblTitle.Size = New-Object System.Drawing.Size(340, 28)
$form.Controls.Add($lblTitle)

# Subtitle
$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Leopold Walli AI Software Productions"
$lblSub.Font = New-Object System.Drawing.Font("Segoe UI", 8.5, [System.Drawing.FontStyle]::Italic)
$lblSub.ForeColor = [System.Drawing.Color]::FromArgb(143, 160, 181)
$lblSub.Location = New-Object System.Drawing.Point(24, 44)
$lblSub.Size = New-Object System.Drawing.Size(340, 20)
$form.Controls.Add($lblSub)

# Language ComboBox (English Default)
$comboLang = New-Object System.Windows.Forms.ComboBox
$comboLang.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
$comboLang.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$comboLang.BackColor = [System.Drawing.Color]::FromArgb(30, 38, 48)
$comboLang.ForeColor = [System.Drawing.Color]::FromArgb(240, 246, 252)
$comboLang.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$comboLang.Location = New-Object System.Drawing.Point(380, 18)
$comboLang.Size = New-Object System.Drawing.Size(140, 26)
$comboLang.Items.Add("🇬🇧 English") | Out-Null
$comboLang.Items.Add("🇩🇪 Deutsch") | Out-Null
$comboLang.SelectedIndex = 0 # English is default
$form.Controls.Add($comboLang)

# Description Text
$lblText = New-Object System.Windows.Forms.Label
$lblText.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$lblText.ForeColor = [System.Drawing.Color]::FromArgb(207, 216, 220)
$lblText.Location = New-Object System.Drawing.Point(24, 80)
$lblText.Size = New-Object System.Drawing.Size(496, 95)
$form.Controls.Add($lblText)

# Buttons
$btnInstall = New-Object System.Windows.Forms.Button
$btnInstall.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$btnInstall.BackColor = [System.Drawing.Color]::FromArgb(41, 128, 185)
$btnInstall.ForeColor = [System.Drawing.Color]::White
$btnInstall.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$btnInstall.FlatAppearance.BorderSize = 0
$btnInstall.Location = New-Object System.Drawing.Point(140, 205)
$btnInstall.Size = New-Object System.Drawing.Size(240, 36)
$btnInstall.DialogResult = [System.Windows.Forms.DialogResult]::Yes
$form.Controls.Add($btnInstall)

$btnCancel = New-Object System.Windows.Forms.Button
$btnCancel.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$btnCancel.BackColor = [System.Drawing.Color]::FromArgb(46, 56, 70)
$btnCancel.ForeColor = [System.Drawing.Color]::White
$btnCancel.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$btnCancel.FlatAppearance.BorderSize = 0
$btnCancel.Location = New-Object System.Drawing.Point(395, 205)
$btnCancel.Size = New-Object System.Drawing.Size(125, 36)
$btnCancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($btnCancel)

$form.AcceptButton = $btnInstall
$form.CancelButton = $btnCancel

# Translation Function
$script:UpdateTexts = {
    if ($comboLang.SelectedIndex -eq 1) {
        # Deutsch
        $form.Text = "Siedler 6 ModManager - Erstkonfiguration"
        $lblText.Text = "Um den Siedler 6 ModManager auszuführen, werden die kostenlose Python-Laufzeitumgebung und PyQt6 benötigt.`n`nMöchtest du die benötigten Komponenten jetzt automatisch installieren lassen?`n(Hinweis: Hierfür ist eine aktive Internetverbindung erforderlich)"
        $btnInstall.Text = "🌐 Jetzt automatisch installieren"
        $btnCancel.Text = "Abbrechen"
    } else {
        # English
        $form.Text = "Settlers 6 ModManager - Prerequisite Setup"
        $lblText.Text = "To run the Settlers 6 ModManager, the free Python runtime and PyQt6 are required.`n`nWould you like to install the required components automatically now?`n(Note: An active internet connection is required)"
        $btnInstall.Text = "🌐 Install Automatically Now"
        $btnCancel.Text = "Cancel"
    }
}

$comboLang.Add_SelectedIndexChanged({
    & $script:UpdateTexts
})

# Initial text update
& $script:UpdateTexts

$result = $form.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
    # If German was selected, write to a temp file so subsequent installer can pick it up
    $langChoice = if ($comboLang.SelectedIndex -eq 1) { "de" } else { "en" }
    $choiceFile = Join-Path $repoDir "ModManager\.setup_lang"
    Set-Content -Path $choiceFile -Value $langChoice -Encoding UTF8
    exit 0
} else {
    exit 1
}
