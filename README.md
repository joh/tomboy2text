# tomboy2text
Converts Tomboy XML files to plain text notes.

Uses Markdown formatting when possible.

Creates subdirectories for notebooks.

```
usage: tomboy2text.py [-o FILE|DIR] notes [notes ...]

positional arguments:
  notes                 Note files

optional arguments:
  -o OUTFILE, --outfile OUTFILE
                        Output file or directory (default: stdout)
  -s SUFFIX, --suffix SUFFIX
                        Output file suffix (default: .txt)
```
