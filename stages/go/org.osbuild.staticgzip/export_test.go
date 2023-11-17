package main

import (
	"io/ioutil"
	"path/filepath"
	"testing"
)

func MockApiArguments(t *testing.T, apiArgs []byte) (restore func()) {
	saved := apiArgumentsPath

	tmpdir := t.TempDir()
	apiArgumentsPath = filepath.Join(tmpdir, "apiArguments")
	if err := ioutil.WriteFile(apiArgumentsPath, apiArgs, 0644); err != nil {
		t.Fatalf("%v", err)
	}

	return func() {
		apiArgumentsPath = saved
	}
}

var (
	ApiArguments = apiArguments
)
