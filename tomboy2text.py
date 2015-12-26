#!/usr/bin/env python3
import sys
import os
import re
import xml.sax
import dateutil.parser

def lstrip(string, prefix):
    if string.startswith(prefix):
        return string[len(prefix):]
    else:
        return string

class TomboyContentHandler(xml.sax.ContentHandler):
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)

        self.list_level = 0
        self.header_level = 0
        self.formatting = []
        self.in_element = None
        self.line = ""

        self.title = ""
        self.content = ""
        self.last_change = None
        self.tags = []

    def startElement(self, name, attrs):
        print("startElement:", name)
        if name in ('title', 'note-content', 'last-change-date', 'tag'):
            self.in_element = name

        if self.in_element is not 'note-content':
            return

        if name == 'list':
            self.list_level += 1
        elif name == 'list-item':
            self.content += '{} '.format('*' * self.list_level)
        elif name == 'bold':
            self.formatting.append('*')
        elif name == 'italic':
            self.formatting.append('_')
        elif name == 'strikethrough':
            self.formatting.append('~~')
        elif name == 'monospace':
            self.formatting.append('`')
        elif name == 'size:huge':
            self.header_level = 1
        elif name == 'size:large':
            self.header_level = 2

    def endElement(self, name):
        print("endElement", name)
        if name in ('title', 'note-content', 'last-change-date', 'tag'):
            self.in_element = None

        if self.in_element is not 'note-content':
            return

        if name == 'list':
            self.list_level -= 1
        elif name == 'bold':
            self.formatting.remove('*')
        elif name == 'italic':
            self.formatting.remove('_')
        elif name == 'strikethrough':
            self.formatting.remove('~~')
        elif name == 'monospace':
            self.formatting.remove('`')
        elif name == 'size:huge':
            self.header_level = 0
        elif name == 'size:large':
            self.header_level = 0

    def format_characters(self, content):
        if not content.strip():
            return content

        pre = "".join(self.formatting)
        post = "".join(self.formatting[::-1])
        return pre + content + post

    def format_line(self, line):
        print("format_line", self.header_level)
        pre = '#' * self.header_level
        return pre + line + "\n"

    def characters(self, content):
        print("characters:", repr(content))
        if self.in_element == 'note-content':
            if content == '\n':
                self.content += self.format_line(self.line)
                self.line = ""
            else:
                self.line += self.format_characters(content)
        elif self.in_element == 'title':
            self.title += content
        elif self.in_element == 'last-change-date':
            self.last_change = dateutil.parser.parse(content)
        elif self.in_element == 'tag':
            self.tags.append(lstrip(content, "system:"))

def parse_note(filename):
    handler = TomboyContentHandler()
    with open(filename) as f:
        xml.sax.parse(f, handler)

    return {'title': handler.title,
            'content': handler.content,
            'last_change': handler.last_change,
            'tags': handler.tags}

def main(args):
    #print args

    outdir = None
    outfile = None

    if len(args.notes) > 1:
        # Directory required for many notes
        outdir = args.outfile
        if os.path.exists(args.outfile):
            assert os.path.isdir(args.outfile)
        else:
            # Create directory
            os.makedirs(args.outfile)

    if os.path.isdir(args.outfile):
        outdir = args.outfile
    elif args.outfile == '-':
        outfile = sys.stdout
    else:
        outfile = open(args.outfile, 'w')

    for notefile in args.notes:
        note = parse_note(notefile)
        content = note['content']
        content += u'\n'.join(['@{}'.format(t) for t in note['tags']])
        content += u'\n'

        if outdir:
            outfile = os.path.join(outdir, note['title'] + args.suffix)
            outfile = open(outfile, 'w')

        outfile.write(content)
        if outfile is not sys.stdout:
            outfile.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Convert Tomboy notes to text')
    parser.add_argument('notes', nargs='+', help='Note files')
    parser.add_argument('-o', '--outfile', default='-',
            help='Output file or directory (default: stdout)')
    parser.add_argument('-s', '--suffix', default='.txt',
            help='Output file suffix (default: %(default)s)')

    args = parser.parse_args()

    main(args)
