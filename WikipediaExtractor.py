#!/usr/bin/env python

import sys
import re

#
## Closure
#
def Closure(string, mark_begin, mark_end):
    # Clean string
    string = string.replace('|-]', '')

    # Extract begin-mark and end-mark
    m1 = [m.span()[0] for m in re.finditer(
        r'%s' % mark_begin\
            .replace('*', '\*')\
            .replace('-', '\-')\
            .replace('{', '\{')\
            .replace('}', '\}')\
            .replace('[', '\[')\
            .replace(']', '\]'),\
        string
    )]
    m2 = [m.span()[0] for m in re.finditer(
        r'%s' % mark_end\
            .replace('*', '\*')\
            .replace('-', '\-')\
            .replace('{', '\{')\
            .replace('}', '\}')\
            .replace('[', '\[')\
            .replace(']', '\]'),\
        string
    )]

    # Build stack for extracting
    stack = []
    i = 0
    j = 0
    m1_length = len(m1)
    m2_length = len(m2)
    while not (i >= m1_length and j >= m2_length):
        if i >= m1_length:
            stack.append((mark_end, m2[j]))
            j += 1
            continue

        if j >= m2_length:
            stack.append((mark_begin, m1[i]))
            i += 1
            continue

        if m1[i] < m2[j]:
            stack.append((mark_begin, m1[i]))
            i += 1
        else:
            stack.append((mark_end, m2[j]))
            j += 1

    # Extract candidates indexes
    _candidates = []
    if len(stack) >= 2:
        mark_begin_num = 0
        mark_end_num = 0
        closure = []
        for mark, index in stack:
            if not closure and mark == mark_begin:
                closure.append(index)

            if mark == mark_begin:
                mark_begin_num += 1
            elif mark == mark_end:
                mark_end_num += 1

            if mark_begin_num == mark_end_num:
                closure.append(index)
                _candidates.append(closure)
                closure = []

    # Filter candidates string
    candidates = []
    for _candidate in _candidates:
        candidate = string[_candidate[0]+len(mark_begin):_candidate[1]]
        candidates.append(candidate)
    return candidates, _candidates

def SortedClosure((candidates, _candidates)):
    # Sort by size reversely
    indexes = sorted([(i, j[1]-j[0]) for i, j in enumerate(_candidates)], key=lambda i:i[1], reverse=True)
    candidates_sorted = []
    _candidates_sorted = []
    for i, j in indexes:
        candidates_sorted.append(candidates[i])
        _candidates_sorted.append(_candidates[i])
    return candidates_sorted, _candidates_sorted

#
## Cleaner
#
def CleanedInfobox(string):
    pattern = re.compile(r"(\[\[)|(\]\])|(''')|(&lt;.*?&gt;)", re.DOTALL)
    string = pattern.sub('', string)

    if '{{' in string:
        entries, _ = SortedClosure(Closure(string, '{{', '}}'))
        for entry in entries:
            string = string.replace('{{' + entry + '}}', '')

    if '-{' in string:
        entries, _ = SortedClosure(Closure(string, '-{', '}-'))
        for entry in entries:
            try:
                string = string.replace('-{' + entry + '}-', entry.split(';')[0].split(':')[1].strip())
            except:
                string = string.replace('-{' + entry + '}-', entry)
    return string

def CleanedText(string):
    pattern = re.compile(r"(''')|(&lt;.*?&gt;)|(^\s?\*\s?)", re.DOTALL|re.MULTILINE)
    string = pattern.sub('', string)

    if '{{' in string:
        entries, _ = SortedClosure(Closure(string, '{{', '}}'))
        for entry in entries:
            string = string.replace('{{' + entry + '}}', '')

    if '{' in string:
        entries, _ = SortedClosure(Closure(string, '{', '}'))
        for entry in entries:
            string = string.replace('{' + entry + '}', '')

    if '[[' in string:
        entries, _ = SortedClosure(Closure(string, '[[', ']]'))
        for entry in entries:
            string = string.replace('[[' + entry + ']]', entry.split('|')[0])

    if '[' in string:
        entries, _ = SortedClosure(Closure(string, '[', ']'))
        for entry in entries:
            string = string.replace('[' + entry + ']', '')

    if '===' in string:
        entries, _ = SortedClosure(Closure(string, '=== ', ' ==='))
        for entry in entries:
            string = string.replace('=== ' + entry + ' ===', entry)

    if '==' in string:
        entries, _ = SortedClosure(Closure(string, '== ', ' =='))
        for entry in entries:
            string = string.replace('== ' + entry + ' ==', entry)

    return re.sub(r'\n{2,}', '\n\n', string)

#
## Id
#
def Id(page):
    matches = re.search(r'<id>(.*?)</id>', page)
    return matches.group(1)

#
## Title
#
def Title(page):
    matches = re.search(r'<title>(.*?)</title>', page)
    return matches.group(1)

#
## Text
#
def Text(page):
    pattern = re.compile(r'<text.*?>(.*?)</text', re.DOTALL)
    matches = pattern.search(page)
    return matches.group(1)

#
## Infobox
#
def InfoBox(page):
    INFOBOX_BEGIN = '{{'
    INFOBOX_END = '}}'

    # Extract infobox candidates
    candidates, _ = Closure(page, INFOBOX_BEGIN, INFOBOX_END)
                
    # Filter valid infobox
    candidate = None
    for _candidate in candidates:
        if '|' in _candidate and '=' in _candidate:
            candidate = _candidate
            break

    # Parse infobox string to object
    infobox = []
    if candidate:
        def parse_infobox(string):
            splitter = '|||'
            entries, _ = Closure(string, '{{', '}}')
            for entry in entries:
                string = string.replace('{{' + entry + '}}', '{{' + entry.replace('|', '$$$') + '}}')

            entries, _ = Closure(string, '[[', ']]')
            for entry in entries:
                string = string.replace('[[' + entry + ']]', '[[' + entry.replace('|', '$$$') + ']]')

            return string.replace('|', splitter).replace('$$$', '|'), splitter
        candidate, splitter = parse_infobox(candidate)

        kvstrings = candidate.split(splitter)
        for kvstring in kvstrings:
            if '=' not in kvstring or (kvstring.lstrip() and kvstring.lstrip()[0] == '{'):
                continue # this line doest have key value
            key, value = kvstring.split('=', 1)
            infobox.append((key.strip(), value.strip()))
    return infobox

#
## Abstract
#
def Abstract(text):
    return text.split('\n')[0]

#
## Category
#
def Category(text):
    matches = re.findall(r'\[\[Category:(.*?)\]\]', text) 
    category = [m for m in matches]
    return category

#
## Entity
#
def Entity(text):
    return ''

class WikipediaExtractor:
    def __init__(self, *args, **kwargs):
        for dictionary in args:
            for key in dictionary:
                setattr(self, key, dictionary[key])        
        for key in kwargs:
            setattr(self, key, kwargs[key])

        if not hasattr(self, 'file'):
            print 'Need argument: file'
            exit(1)

        if hasattr(self, 'min_infobox'):
            try:
                int(self.min_infobox)
            except:
                print 'Argument min_infobox must be integer'
                exit(1)

        if hasattr(self, 'clean_infobox'):
            if type(self.clean_infobox) != bool:
                print 'Argument clean_infobox must be bool'
                exit(1)

        if hasattr(self, 'clean_text'):
            if type(self.clean_text) != bool:
                print 'Argument clean_text must be bool'
                exit(1)

        self.file_handle = open(self.file, 'r')

        flag = False
        page = []
        count = 0

        for i in range(10000):
            line = self.file_handle.readline()

            if line.lstrip().startswith('<page>'):
                page = [line]
                flag = True
                continue

            if line.rstrip().endswith('</page>'):
                page.append(line)
                flag = False

                count += 1
                page = ''.join(page)

                id = Id(page)
                title = Title(page)
                text = CleanedText(Text(page)) if self.clean_text else Text(page)
                infobox = InfoBox(text)
                abstract = Abstract(text)
                category = Category(text)
                entity = Entity(text)

                print '@@ENTRY'
                print '@@Id'
                print id
                print '@@Title'
                print title
                print '@@Text'
                print  text
                print '@@InfoBox'
                if len(infobox) >= self.min_infobox:
                    for key, value in infobox:
                        if self.clean_infobox:
                            print '%s:%s' % (CleanedInfobox(key), CleanedInfobox(value))
                        else:
                            print '%s:%s' % (key, value)
                print '@@Abstract'
                print abstract
                print '@@Category'
                print ';'.join(category)
                print '@@ENDENTRY'
                continue

            if flag:
                page.append(line)
                continue


    def __del__(self):
        self.file_handle.close()

    def _extract_title(self):
        pass

    def _extract_string(self):
        pass

    def _extract_introduction(self):
        pass

    def _extract_category(self):
        pass

if __name__ == '__main__':
    filename = sys.argv[1]
    WikipediaExtractor(
        file=filename,
        min_infobox=2,
        clean_infobox=False,
        clean_text=True
    )
