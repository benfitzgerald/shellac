#!/usr/bin/python

from cmd import Cmd
import readline
import inspect


def completer(func):
    def innerCompleter(obj):
        if not hasattr(obj, "completions"):
            obj.completions = []
        obj.completions.append(func)
        return obj
    return innerCompleter


def members(obj):
    for f in inspect.getmembers(obj):
        if f[0].startswith('do_'):
            yield f[0][3:]


def complete_list(l, token):
    for x in l:
        if x.startswith(token):
            yield x + ' '


class Shellac(Cmd):

    def do_exit(self, args):
        return True

    do_EOF = do_exit

    def do_help(self, args):
        if args:
            root = self
            items = args.split(' ')
            for item in items:
                if not item.isspace():
                    try:
                        root = getattr(root, 'do_' + item)
                    except AttributeError:
                        print "*** Syntax Error: No command", item
                        break
                # FIX: Corner cases where item is not a unique string in args?
                if items[-1] == item:
                    help_string = None
                    try:
                        help_string = getattr(root, '__doc__')
                    except AttributeError:
                        pass
                    if help_string is None:
                        print "*** no help on", item
                    else:
                        print "Help for %s: %s" % (item, help_string)
        else:
            print "Help's help"

    def onecmd(self, line, args='', root=None):
        if not args:
            args = line
        if not root:
            root = self
        if args:
            child, _, args = args.partition(' ')
        elif not line:
            return self.emptyline()
        self.lastcmd = line
        if line == 'EOF':  # http://bugs.python.org/issue13500
            self.lastcmd = ''
        try:
            root = getattr(root, 'do_' + child)
        except AttributeError:
            return self.default(line)
        if inspect.isclass(root):
            # If a class, we must instantiate it
            root = root()
        try:
            # Is root (really) callable
            return root(args)
        # python2 and 3 return different exceptions here
        except (AttributeError, TypeError):
            # It wasn't callable, recurse
            if not args:
                return self.default(line)
            return self.onecmd(line, args, root)

    # traverse_help is recursive so needs to find itself through the class
    @classmethod
    def traverse_help(cls, tokens, tree):
        # Strip 'help' off the tokens list
        if tokens[0] == "help":
            tokens = tokens[1:]
        if tree is None:
            return []
        elif len(tokens) == 0:
            return members(tree)
        if len(tokens) == 1:
            return complete_list(members(tree), tokens[0])
        elif tokens[0] in members(tree):
            return cls.traverse_help(tokens[1:],
                                     getattr(tree, 'do_' + tokens[0]))
        return []

    # traverse_do is recursive so needs to find itself through the class
    @classmethod
    def traverse_do(cls, tokens, tree):
        if tree is None:
            return []
        elif len(tokens) == 0:
            return members(tree)
        if len(tokens) == 1:
            if hasattr(tree, 'completions'):
                complist = []
                for f in getattr(tree, 'completions'):
                    complist.extend(f(tokens[0]))
                return complist
            return complete_list(members(tree), tokens[0])
        elif tokens[0] in members(tree):
            return cls.traverse_do(tokens[1:],
                                   getattr(tree, 'do_' + tokens[0]))
        return []

    def complete(self, text, state):
        if state == 0:
            endidx = readline.get_endidx()
            buf = readline.get_line_buffer()
            tokens = buf[:endidx].split()
            if not tokens or buf[endidx - 1] == ' ':
                tokens.append('')
            cmd = tokens[0]
            if cmd == "help":
                self.results = list(self.traverse_help(tokens, self))
            else:
                self.results = list(self.traverse_do(tokens, self))
        try:
            return self.results[state]
        except IndexError:
            return None
