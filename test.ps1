function testfile {
	param (
		[string]$file,
		[string]$input_str,
		[switch]$time
	)
	$out = ""
	
	if ($time) {
		$m = ""
		if ([string]::IsNullOrEmpty($input)) {
			$m = Measure-Command {$out = ( $input_str | & py main.py -s $file --run)}
		} else {
			$m = Measure-Command {$out = (& py main.py -s $file --run)}
		}
		$out
		"Time:"
		$m.TotalSeconds
	}
	else {
		if ([string]::IsNullOrEmpty($input)) {
			$out = ( $input_str | & py main.py -s $file --run)
		} else {
			$out = (& py main.py -s $file --run)
		}
		return $out
	}
}

function TestAll {
	
	# (file name, expected output, optional input string)
	$files = (
		(
			"string.pop",
			"hello`nMatch",
			"hello"
		),
		(
			"vector.pop",
			"Init called.`npushed data: 0, 1, 2`nvector top: 9999998`ncapacity: 16777216`nend."
		),
		(
			"realloc.pop",
			"malloc 100`nrealloc1 200`nrealloc2 300`nvector data: 100, 200, 300`nend"
		),
		(
			"node.pop",
			"node_value: 1`nnode_value: 2"
		)
	)
	$passed_tests = 0
	foreach ($currtest in $files) {
		if ($currtest.Length -eq 3) {
			$out = (testfile -file $currtest[0] -input_str $currtest[2]) -join "`n"
			if ($out -eq $currtest[1]) {
				"`nTest [" + $currtest[0] + "] passed"
				$passed_tests += 1
			} else {
				"__________________________________"
				"Test [" + $currtest[0] + "] failed"
				"=================================="
				"Expected:"
				$currtest[1]
				"----------------------------------"
				"Recieved:"
				$out
				"=================================="
			}
		} else {
			$out = (testfile -file $currtest[0]) -join "`n"
			if ($out -eq $currtest[1]) {
				"`nTest [" + $currtest[0] + "] passed"
				$passed_tests += 1
			} else {
				"Test [" + $currtest[0] + "] failed"
				"`tExpected:"
				$currtest[1]
				"`tRecieved:"
				$out
			}
		}
	}
	"`n-------------------`nPassed Tests: " + $passed_tests + " / " + $files.Length + "`n-------------------"
}
