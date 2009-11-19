#
# Copyright (C) 2006 Async Open Source
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
# USA
#
# Author(s): Johan Dahlin <[EMAIL PROTECTED]>
#

import string
import sys

import gobject
import pango
import gtk

class MaskError(Exception):
    pass

(INPUT_CHARACTER,
 INPUT_ALPHA,
 INPUT_DIGIT) = range(3)

INPUT_FORMATS = {
    'a': INPUT_ALPHA,
    'd': INPUT_DIGIT,
    'c': INPUT_CHARACTER,
    }

class MaskEntry(gtk.Entry):
    def __init__(self):
        gtk.Entry.__init__(self)
        # It only makes se
        self.modify_font(pango.FontDescription("monospace"))

        self.connect('insert-text', self._on_insert_text)
        self.connect('delete-text', self._on_delete_text)

        # List of validators
        #  str -> static characters
        #  int -> dynamic, according to constants above
        self._validators = []
        self._interactive_input = True
        self._mask = None

    # Callbacks

    def _on_insert_text(self, editable, new, length, position):
        if not self._interactive_input:
            return

        if length != 1:
            print 'TODO: paste'
            self.stop_emission('insert-text')
            return

        position = self.get_position()
        next = position + 1
        validators = self._validators
        if len(validators) <= position:
            self.stop_emission('insert-text')
            return

        validator = validators[position]
        if validator == INPUT_CHARACTER:
            # Accept anything
            pass
        elif validator == INPUT_ALPHA:
            if not new in string.lowercase:
                self.stop_emission('insert-text')
                return
        elif validator == INPUT_DIGIT:
            if not new in string.digits:
                self.stop_emission('insert-text')
                return
        elif isinstance(validator, str):
            self.set_position(next)
            self.stop_emission('insert-text')
            return

        self.delete_text(position, next)

        # If the next position is a static character and
        # the one after the next is input, skip over
        # the static character
        if len(validators) > next + 1:
            if (isinstance(validators[next], str) and
                isinstance(validators[next+1], int)):
                # Ugly: but it must be done after the parent
                #       inserts the text
                gobject.idle_add(self.set_position, next+1)

    def _on_delete_text(self, editable, start, end):
        if not self._interactive_input:
            return
        if end - start != 1:
            print 'TODO: cut/delete several'
            self.stop_emission('delete-text')
            return

        validator = self._validators[start]
        if isinstance(validator, str):
            self.set_position(start)
            self.stop_emission('delete-text')
            return

        self.insert_text(' ', end)
        return False

    # Public API

    def set_mask(self, mask):
        """
        Sets the mask of the Entry.
        The format of the mask is similar to printf, but the
        only supported format characters are:
        - 'd' digit
        - 'a' alphabet, honors the locale
        - 'c' any character
        A digit is supported after the control.
        Example mask for a ISO-8601 date
        >>> entry.set_mask('%4d-%2d-%2d')

        @param mask: the mask to set
        """

        self._mask = mask
        if not mask:
            return

        input_length = len(mask)
        keys = INPUT_FORMATS.keys()
        lenght = 0
        pos = 0
        while True:
            if pos >= input_length:
                break
            if mask[pos] == '%':
                s = ''
                format_char = None
                # Validate/extract format mask
                pos += 1
                while True:
                    if mask[pos] not in string.digits:
                        raise MaskError(
                            "invalid format padding character: %s" % mask[pos])
                    s += mask[pos]
                    if mask[pos+1] in INPUT_FORMATS:
                        format_char = mask[pos+1]
                        break
                    pos += 1
                pos += 1
                self._validators += [INPUT_FORMATS[format_char]] * int(s)
            else:
                self._validators.append(mask[pos])
            pos += 1

        s = ''
        for validator in self._validators:
            if isinstance(validator, int):
                s += '_'
            elif isinstance(validator, str):
                s += validator
            else:
                raise AssertionError
        self.set_text(s)

    def get_field_text(self):
        """
        Get the fields assosiated with the entry
        if a field is empty it'll return an empty string
        otherwise it'll include the content

        @returns: fields
        @rtype: list of strings
        """
        if not self._mask:
            raise MaskError("a mask must be set before calling get_field_text")

        def append_field(fields, field_type, s):
            if s.count(' ') == len(s):
                s = ''
            if field_type == INPUT_DIGIT:
                s = int(s)
            fields.append(s)

        fields = []
        pos = 0
        s = ''
        field_type = -1
        text = self.get_text()
        validators = self._validators
        while True:
            if pos >= len(validators):
                append_field(fields, field_type, s)
                break

            validator = validators[pos]
            if isinstance(validator, int):
                s += text[pos]
                field_type = validator
            else:
                append_field(fields, field_type, s)
                s = ''
                field_type = -1
            pos += 1

        return fields

    def set_text(self, text):
        """
        Sets the text of the entry

        @param text:
        """
        self._interactive_input = False
        try:
            gtk.Entry.set_text(self, text)
        finally:
            self._interactive_input = True

    def delete_text(self, start, end):
        """
        Deletes text at a certain range

        @param start:
        @param end:
        """
        self._interactive_input = False
        try:
            gtk.Entry.delete_text(self, start, end)
        finally:
            self._interactive_input = True

    def insert_text(self, text, position=0):
        """
        Insert text at a specific position

        @param text:
        @param position:
        """
        self._interactive_input = False
        try:
            gtk.Entry.insert_text(self, text, position)
        finally:
            self._interactive_input = True