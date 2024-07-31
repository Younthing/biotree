# `biotree`

Biotree CLI: A command line interface for Biotree operations

**Usage**:

```console
$ biotree [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `-v, --version`: Show the application's version and exit
- `--help`: Show this message and exit.

**Commands**:

- `target`: Commands for SMILES to target predictions

## `biotree target`

Commands for SMILES to target predictions

**Usage**:

```console
$ biotree target [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--help`: Show this message and exit.

**Commands**:

- `prediction`

### `biotree target prediction`

**Usage**:

```console
$ biotree target prediction [OPTIONS]
```

**Options**:

- `-s, --smiles TEXT`: List of SMILES strings separated by commas
- `-f, --file PATH`: Path to a file containing SMILES strings
- `--help`: Show this message and exit.
