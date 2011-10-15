param([switch]$DontUpload=$False)

$here = $MyInvocation.MyCommand.Definition
$here = split-path $here -parent
$root = resolve-path (join-path $here "..")

push-location $root
	# rename all .tmLanguage so they don't show up in syntax menu
	get-childitem ".\Support\*.tmLanguage" | `
						foreach-object { copy-item $_ ($_ -replace '.tmLanguage','.hidden-tmLanguage') }
	if (-not (test-path (join-path $root "Doc"))) {
		new-item -itemtype "d" -name "Doc" > $null
		copy-item ".\Data\main.css" ".\Doc"
	}

	# Generate docs in html from rst.
	push-location ".\Doc"
		get-childitem "..\*.rst" | foreach-object {
									& "rst2html.py" `
											"--template" "..\data\html_template.txt" `
											"--stylesheet-path" "main.css" `
											"--link-stylesheet" `
											$_.fullname "$($_.basename).html"
								}
	pop-location

	# Ensure MANIFEST reflects all changes to file system.
	remove-item ".\MANIFEST" -erroraction silentlycontinue
	start-process "python" -argumentlist ".\setup.py","spa" -NoNewWindow -Wait

	(get-item ".\dist\SublimeHg.sublime-package").fullname | clip.exe
	# make sure we don't create conflicts with our installation
	write-host "Removing generated *.hidden.tmLanguage files."
	remove-item "./Support/*.hidden-tmLanguage"
pop-location

if (-not $DontUpload) {
	start-process "https://bitbucket.org/guillermooo/sublimehg/downloads"
}
