def flatten(t: list[list[any]]) -> list[any]:
    return [item for sublist in t for item in sublist]


def write_to_file(filepath: str, contents: str):
    with open(filepath, 'w') as f:
        f.seek(0)
        f.write(contents)
        f.truncate()
