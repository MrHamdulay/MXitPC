import re
def _parse(line, command):
    replacement = ''
    if command['type'] == 'reply':
        replacement = '<a href="send|%s">%s</a>' % (command['replymsg'], command['selmsg'])

    return replacement 


def parse(message):
    lines = message.split('\n')
    for line in lines:
        pos = line.find('::op=cmd')
        if pos == -1:
            continue
        beginning = line[:pos]
        endpos = line.find(':', pos+9)
        commands = line[pos+9:]
        commands = commands.split('|')
        commands[-1], leftover = commands[-1].split(':')
        commands = [command.split('=') for command in commands]
        tempdict = {}
        for command in commands:
            tempdict[command[0]] = command[1]
        commands = tempdict

        replacement = _parse(line, commands)
        lines[lines.index(line)] = beginning + replacement + leftover

    return '<br />\n'.join(lines)

