package main_test

import (
	"reflect"
	"testing"

	main "org.osbuild.stages/staticgzip"
)

var fakeInput = []byte(`
{
  "tree": "/run/osbuild/tree",
  "paths": {
    "devices": "/dev",
    "inputs": "/run/osbuild/inputs",
    "mounts": "/run/osbuild/mounts"
  },
  "devices": {},
  "inputs": {
    "file": {
      "path": "/run/osbuild/inputs/file",
      "data": {
        "files": {
          "sha256:f950375066d74787f31cbd8f9f91c71819357cad243fb9d4a0d9ef4fa76709e0": {}
        }
      }
    }
  },
  "mounts": {},
  "options": {
    "filename": "compressed.gz"
  },
  "meta": {
    "id": "6dc907e7cf7b6436938d55eabad9209d4d4b7c4f338f3eef20f1d212aca48c79"
  }
}
`)

func TestApiArguments(t *testing.T) {
	restore := main.MockApiArguments(t, fakeInput)
	defer restore()

	args, err := main.ApiArguments()
	if err != nil {
		t.Fatalf("%v", err)
	}
	if args.Inputs.File.Path != "/run/osbuild/inputs/file" {
		t.Fatalf("unexpected args %v", args)
	}
	expected := map[string]interface{}{
		"sha256:f950375066d74787f31cbd8f9f91c71819357cad243fb9d4a0d9ef4fa76709e0": map[string]interface{}{},
	}
	input := args.Inputs.File.Data.Files
	if !reflect.DeepEqual(input, expected) {
		t.Fatalf("unexpected args %v", args)
	}
	if args.Options.Filename != "compressed.gz" {
		t.Fatalf("unexpected args %v", args)
	}
}
