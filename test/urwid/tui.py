#!/usr/bin/env python3

import urwid


class ViewTerminal(urwid.Terminal):
    _selectable = False


def main():
    urwid.set_encoding('utf8')
    geth_log = ViewTerminal(['tail', '-f', '/tmp/geth.log'], encoding='utf-8')

    edit = urwid.Edit('focus test edit: ')
    status = urwid.Filler(edit)

    mainframe = urwid.LineBox(
        urwid.Pile([
            ('weight', 3, status),
            ('fixed', 10, urwid.LineBox(geth_log, title="geth")),
        ], focus_item=status),
        title="elcaro oracle",
    )

    def handle_key(key):
        print(key)
        if key in 'q' or 'Q':
            raise urwid.ExitMainLoop()

    loop = urwid.MainLoop(
        mainframe,
        handle_mouse=True,
        unhandled_input=handle_key)

    geth_log.main_loop = loop
    loop.run()


if __name__ == '__main__':
    main()
