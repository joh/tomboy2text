#!/usr/bin/env python3
# encoding=utf8
"""
tomboy2text: Convert Tomboy XML to plain text
"""
import sys
import os
import re
import xml.sax
import dateutil.parser
import time

def lstrip(string, prefix):
    if string.startswith(prefix):
        return string[len(prefix):]
    else:
        return string

def safe_filename(filename):
    filename = filename.replace('/', ' ')
    keepchars = (' ','.','_')
    return "".join(c for c in filename if c.isalnum() or c in keepchars).rstrip()

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
        self.notebook = None
        self.tags = []

    def startElement(self, name, attrs):
        #print("startElement:", name)
        if name in ('title', 'note-content', 'last-change-date', 'tag'):
            self.in_element = name

        if self.in_element != 'note-content':
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
        #print("endElement", name)
        if name in ('title', 'note-content', 'last-change-date', 'tag'):
            self.in_element = None

        if self.in_element != 'note-content':
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
        #print("format_characters", content, self.formatting)
        if not content.strip():
            return content

        pre = "".join(self.formatting)
        post = "".join(self.formatting[::-1])
        return pre + content + post

    def format_line(self, line):
        #print("format_line", self.header_level)
        pre = '#' * self.header_level
        return pre + line + "\n"

    def characters(self, content):
        #print("characters:", repr(content))
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
            tag = lstrip(content, "system:")
            if tag.startswith("notebook:"):
                self.notebook = lstrip(tag, "notebook:")
            else:
                self.tags.append(tag)

def parse_note(filename):
    handler = TomboyContentHandler()
    with open(filename) as f:
        xml.sax.parse(f, handler)

    return {'title': handler.title,
            'content': handler.content,
            'last_change': handler.last_change,
            'notebook': handler.notebook,
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

    if os.path.isdir(args.outfile):
        outdir = args.outfile

    if not outdir:
        if args.outfile == '-':
            outfile = sys.stdout
        else:
            outfile = open(args.outfile, 'w')

    for notefile in args.notes:
        note = parse_note(notefile)
        content = note['content']
        content += u'\n'.join(['@{}'.format(t) for t in note['tags']])
        content += u'\n'

        if outdir:
            od = outdir
            if note['notebook']:
                od = os.path.join(outdir, safe_filename(note['notebook']))

            filename = safe_filename(note['title'] + args.suffix)
            outpath = os.path.join(od, filename)

            if not os.path.isdir(od):
                os.makedirs(od)

            outfile = open(outpath, 'w')
        else:
            outpath = args.outfile

        outfile.write(content.encode("utf-8"))
        if outfile is not sys.stdout:
            outfile.close()

            if note['last_change']:
                mtime = time.mktime(note['last_change'].timetuple())
                os.utime(outpath, (mtime, mtime))



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Convert Tomboy notes to plain text')
    parser.add_argument('notes', nargs='+', help='Note files')
    parser.add_argument('-o', '--outfile', default='-',
            help='Output file or directory (default: stdout)')
    parser.add_argument('-s', '--suffix', default='.txt',
            help='Output file suffix (default: %(default)s)')

    args = parser.parse_args()

    main(args)
