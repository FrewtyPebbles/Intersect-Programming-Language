function testfile {
	param (
		[string]$file,
		[string]$inputstr,
		[switch]$time,
		[switch]$ir
	)
	$out = ""
	$show_ir = ""
	$cmd = "py main.py -s `"./test/$($file).pop`" -o `"./test_binaries/$($file)`" --run $($show_ir)"
	if ($ir) {
		$show_ir = "--ir"
	}
	if (![string]::IsNullOrEmpty($inputstr)) {
		$cmd = "`"$($inputstr)`" | $($cmd)"
	}
	if ($time) {
		$m = Measure-Command {$out = iex $cmd }
		$out
		"Time:"
		$m.TotalSeconds
	} else {
		$out = iex $cmd
		$out
	}
}

function testall {
	
	# (file name, expected output, optional input string)
	$files = (
		(
			"string",
			"hello`nMatch",
			"hello"
		),
		(
			"vector",
			"Init called.`npushed data: 0, 1, 2`nvector top: 9999998`ncapacity: 16777216`nend."
		),
		(
			"realloc",
			"malloc 100`nrealloc1 200`nrealloc2 300`nvector data: 100, 200, 300`nend"
		),
		(
			"node",
			"node_value: 1`nnode_value: 2"
		),
		(
			"nested_struct",
			"Init called.`nget 0: 10`nget 0 and 1: 10 and 20`nend."
		),
		(
			"struct",
			"value: 5"
		),
		(
			"hashmap",
			"thing one = 100`nthing two = 200"
		),
		(
			"operator",
			"new_store: 3"
		),
		(
			"vtable",
			"data: 5`ndata: 7"
		)
	)
	$passed_tests = 0
	$char_width = $(Get-Host).UI.RawUI.WindowSize.Width
	foreach ($currtest in $files) {
		if ($currtest.Length -eq 3) {
			$out = (& testfile -file $currtest[0] -inputstr $currtest[2]) -join "`n"
			if ($out -eq $currtest[1]) {
				"`nTest [" + $currtest[0] + "] passed"
				$passed_tests += 1
			} else {
				"_" * $char_width
				"Test [" + $currtest[0] + "] failed"
				"=" * $char_width
				"Expected:"
				$currtest[1]
				"-" * $char_width
				"Recieved:"
				$out
				"=" * $char_width
			}
		} else {
			$out = (& testfile -file $currtest[0]) -join "`n"
			if ($out -eq $currtest[1]) {
				"`nTest [" + $currtest[0] + "] passed"
				$passed_tests += 1
			} else {
				""
				"X" * $char_width
				"X" * $char_width
				"Test [" + $currtest[0] + "] failed"
				"=" * $char_width
				"Expected:"
				$currtest[1]
				"~" * $char_width
				"Recieved:"
				$out
				"=" * $char_width
				"X" * $char_width
				"X" * $char_width
			}
		}
	}
	""
	$passed_tests_str = "| Passed Tests: " + $passed_tests + " / " + $files.Length + " |"
	"-" * $passed_tests_str.Length
	$passed_tests_str
	"-" * $passed_tests_str.Length
}

