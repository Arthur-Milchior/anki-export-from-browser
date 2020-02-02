# -*- coding: utf-8 -*-
# Copyright: Arthur Milchior arthur@milchior.fr
# encoding: utf8
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Feel free to contribute to this code on https://github.com/Arthur-Milchior/anki-export-from-browser
# Add-on number 1983204951 https://ankiweb.net/shared/info/1983204951


from anki.exporting import Exporter, AnkiExporter
from anki.utils import ids2str
from aqt import mw
import typing
import os
from anki.storage import Collection

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

def exportInto(self, path: str) -> None:
    # sched info+v2 scheduler not compatible w/ older clients
    self._v2sched = self.col.schedVer() != 1 and self.includeSched

    # create a new collection at the target
    try:
        os.unlink(path)
    except (IOError, OSError):
        pass
    self.dst = Collection(path)
    self.src = self.col
    # find cards
    cids = self.cardIds()
    # copy cards, noting used nids
    nids = {}
    data = []
    for row in self.src.db.execute(
        "select * from cards where id in " + ids2str(cids)
    ):
        nids[row[1]] = True
        data.append(row)
        # clear flags
        row = list(row)
        row[-2] = 0
    self.dst.db.executemany(
        "insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", data
    )
    # notes
    strnids = ids2str(list(nids.keys()))
    notedata = []
    for row in self.src.db.all("select * from notes where id in " + strnids):
        # remove system tags if not exporting scheduling info
        if not self.includeSched:
            row = list(row)
            row[5] = self.removeSystemTags(row[5])
        notedata.append(row)
    self.dst.db.executemany(
        "insert into notes values (?,?,?,?,?,?,?,?,?,?,?)", notedata
    )
    # models used by the notes
    mids = self.dst.db.list("select distinct mid from notes where id in " + strnids)
    # card history and revlog
    if self.includeSched:
        data = self.src.db.all("select * from revlog where cid in " + ids2str(cids))
        self.dst.db.executemany(
            "insert into revlog values (?,?,?,?,?,?,?,?,?)", data
        )
    else:
        # need to reset card state
        self.dst.sched.resetCards(cids)
    # models - start with zero
    self.dst.models.models = {}
    for m in self.src.models.all():
        if int(m["id"]) in mids:
            self.dst.models.update(m)
    # decks
    dids = self.deckIds()
    print(f"dids is {dids}")
    dconfs = {}
    for d in self.src.decks.all():
        if str(d["id"]) == "1":
            continue
        if dids and d["id"] not in dids:
            continue
        if not d["dyn"] and d["conf"] != 1:
            if self.includeSched:
                dconfs[d["conf"]] = True
        if not self.includeSched:
            # scheduling not included, so reset deck settings to default
            d = dict(d)
            d["conf"] = 1
        self.dst.decks.update(d)
    # copy used deck confs
    for dc in self.src.decks.allConf():
        if dc["id"] in dconfs:
            self.dst.decks.updateConf(dc)
    # find used media
    media = {}
    self.mediaDir = self.src.media.dir()
    if self.includeMedia:
        for row in notedata:
            flds = row[6]
            mid = row[2]
            for file in self.src.media.filesInStr(mid, flds):
                # skip files in subdirs
                if file != os.path.basename(file):
                    continue
                media[file] = True
        if self.mediaDir:
            for fname in os.listdir(self.mediaDir):
                path = os.path.join(self.mediaDir, fname)
                if os.path.isdir(path):
                    continue
                if fname.startswith("_"):
                    # Scan all models in mids for reference to fname
                    for m in self.src.models.all():
                        if int(m["id"]) in mids:
                            if self._modelHasMedia(m, fname):
                                media[fname] = True
                                break
    self.mediaFiles = list(media.keys())
    self.dst.crt = self.src.crt
    # todo: tags?
    self.count = self.dst.cardCount()
    self.dst.setMod()
    self.postExport()
    self.dst.close()

def deckIds(self) -> typing.List[int]:
    dids: List[int]
    if self.did:
        return [self.did] + [x[1] for x in self.src.decks.children(self.did)]
    elif self.cids:
        return self.col.db.list(f"SELECT did FROM cards where id in {ids2str(self.cids)}")
    else:
        return []

AnkiExporter.deckIds = deckIds
AnkiExporter.exportInto = exportInto
