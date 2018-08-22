# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django import forms


class FilterForm(forms.Form):
    @property
    def fields(self):
        return

    @fields.setter
    def fields(self, value):
        pass
