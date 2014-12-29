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
            .replace('{', '\{')\
            .replace('}', '\}')\
            .replace('[', '\[')\
            .replace(']', '\]'),\
        string
    )]
    m2 = [m.span()[0] for m in re.finditer(
        r'%s' % mark_end\
            .replace('*', '\*')\
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

#
## Cleaner
#
def Clean(string):
    entries, _ = Closure(string, '[[', ']]')
    for entry in entries:
        string = string.replace('[[' + entry + ']]', ' ' + entry.split('|')[0])

    entries, _ = Closure(string, '{{', '}}')
    for entry in entries:
        string = string.replace('{{' + entry + '}}', ' ' + entry.split('|')[0])

    entries, _ = Closure(string, '-{', '}-')
    for entry in entries:
        string = string.replace('-{' + entry + '}-', ' ' + entry.split(';')[0].split(':')[1])

    entries, _ = Closure(string, '[', ']')
    for entry in entries:
        string = string.replace('[' + entry + ']', ' ' + entry.split(' ', 1)[-1])
    
    string = re.sub(r'(&lt;br /&gt;)', '\n', string)
    string = re.sub(r"(''')|('')|(&lt;.*?&gt;)", '', string)

    entries = re.findall(r'\[(.+)', string)
    for entry in entries:
        string = string.replace('[' + entry, ' ' + entry.split(' ', 1)[-1])

    return string

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
        # Clean candidate
        candidate = Clean(candidate)

        kvstrings = candidate.split('|')
        for kvstring in kvstrings:
            if '=' not in kvstring:
                continue # this line doest have key value
            key, value = kvstring.split('=', 1)
            infobox.append((key.strip(), value.strip().replace('\n', ';')))
    return infobox

#
## Content
#
def Content(text):
    INFOBOX_BEGIN = '{{'
    INFOBOX_END = '}}'

    # Extract infobox candidates
    _, indexes = Closure(text, INFOBOX_BEGIN, INFOBOX_END)

    # Exclude infobox
    new_indexes = []
    if indexes:
        indexes = reduce(lambda x, y: x+y, indexes)

        if indexes[0] != 0:
            indexes = [0] + indexes
        else:
            del indexes[0]

        if (len(indexes) + 1) % 2:
            indexes.append(indexes[-1]+1)
        indexes.append(-1)

        i = 0
        while i < len(indexes):
            if indexes[i] != indexes[i+1]:
                new_indexes.append((indexes[i], indexes[i+1]))
            i += 2

    # filter content
    content = []
    for begin, end in new_indexes:
        content.append(text[begin+len(INFOBOX_BEGIN):end])
    return ''.join(content)

#
## Category
#
def Category(text):
    return ''

#
## Entity
#
def Entity(text):
    return ''

class WikipediaExtractor:
    def __init__(self, wikidumps_file, infobox_filter=True):
        self.file_handle = open(wikidumps_file, 'r')

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
                text = Text(page)
                infobox = InfoBox(text)
                content = Content(text)

                category = Category(text)
                entity = Entity(text)

                is_valid_infobox = False
                if infobox_filter:
                    validnum = len([value for key, value in infobox if 'zh-' not in value])
                    is_valid_infobox = validnum > len(infobox) / 2

                if not infobox_filter or is_valid_infobox:
                    print 'Count:', count
                    print 'Title:', title
                    print 'InfoBox:', infobox
                    print 'Content:'
                    print content
                    for key, value in infobox:
                        print '  %s = %s' % (key, value)
                    print '-------------------------'
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
    WikipediaExtractor(filename)
