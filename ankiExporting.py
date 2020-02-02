# -*- coding: utf-8 -*-
# Copyright: Arthur Milchior arthur@milchior.fr
# encoding: utf8
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Feel free to contribute to this code on https://github.com/Arthur-Milchior/anki-export-from-browser
# Add-on number 1983204951 https://ankiweb.net/shared/info/1983204951


from anki.exporting import Exporter
from anki.utils import ids2str
from aqt import mw

oldInit = Exporter.__init__
def __init__(self,*args, **kwargs):
    oldInit(self, *args, **kwargs)
    self.cids = None
Exporter.__init__ = __init__

def needSiblings(self):
    userOption = mw.addonManager.getConfig(__name__)
    siblings = userOption["siblings"]
    r=siblings.get(self.key)
    if r is None:
        r= siblings.get("default")
    if r is None:
        r = True
    return r
Exporter.needSiblings = needSiblings

def siblings(cids):
    siblings = mw.col.db.list(f"select id from cards where nid in (select nid from cards where id in {ids2str(cids)})")
    return siblings

oldCardIds= Exporter.cardIds
def cardIds(self):
    if self.cids is not None:
        cids= self.cids
        self.count = len(cids)
    else:
        cids=oldCardIds(self)
    if self.needSiblings():
        cids = siblings(cids)
    return cids
Exporter.cardIds = cardIds
