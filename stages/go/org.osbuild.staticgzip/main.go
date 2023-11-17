package main

import (
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

type apiArgs struct {
	Tree   string `json:"tree"`
	Inputs struct {
		File struct {
			Path string `json:"path"`
			Data struct {
				Files map[string]interface{} `json:"files"`
			} `json:"data"`
		} `json:"file"`
	} `json:"inputs"`
	Options struct {
		Filename string `json:"filename"`
	} `json:"options"`
}

var apiArgumentsPath = "/run/osbuild/api/arguments"

func parseInputs(args *apiArgs) (string, error) {
	files := args.Inputs.File.Data.Files
	if len(files) != 1 {
		return "", fmt.Errorf("unexpected amount of destination files %q", files)
	}
	// XXX: fugly
	var file string
	for k, _ := range files {
		file = k
	}

	path := filepath.Join(args.Inputs.File.Path, file)
	return path, nil
}

func apiArguments() (*apiArgs, error) {
	f, err := os.Open(apiArgumentsPath)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	// alternatively we could unmarshal to map[string]interface{} and
	// poke around via type assertions but that is also not fun
	var data apiArgs
	dec := json.NewDecoder(f)
	if err := dec.Decode(&data); err != nil {
		return nil, err
	}

	return &data, nil
}

func run() error {
	args, err := apiArguments()
	if err != nil {
		return err
	}
	output := args.Tree
	filename := args.Options.Filename
	source, err := parseInputs(args)
	if err != nil {
		return err
	}
	target := filepath.Join(output, filename)

	inf, err := os.Open(source)
	if err != nil {
		return err
	}
	defer inf.Close()
	outf, err := os.Create(target)
	if err != nil {
		return err
	}
	w := gzip.NewWriter(outf)
	if _, err := io.Copy(w, inf); err != nil {
		return err
	}

	return nil
}

func main() {
	if err := run(); err != nil {
		panic(err)
	}
}
